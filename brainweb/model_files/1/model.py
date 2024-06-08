import os
from glob import glob
import numpy as np
import monai
import torch
from PIL import Image
import nibabel as nib
from monai.data import ArrayDataset, decollate_batch, DataLoader
from monai.inferers import sliding_window_inference
from monai.transforms import Activations, AsDiscrete, Compose, LoadImage, ScaleIntensity
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from mayavi import mlab

def load_nii_file(file_path):
    try:
        return nib.load(file_path)
    except Exception as e:
        print(f"Error loading NIfTI file: {e}")
        return None

def plot_and_save_3d(image_data):
    angles = [
    (180, 90, 'On'),
    (90, 90, 'Yan'),
    (180, 0, 'Ust') ]

    for azimuth, elevation, view_name in angles:
        fig = mlab.figure(size=(1000, 800), bgcolor=(1, 1, 1))
        src = mlab.pipeline.scalar_field(image_data)
        src.spacing = [1, 1, 1]
        surf = mlab.pipeline.iso_surface(src, opacity=0.5, colormap='inferno')
        surf.actor.property.interpolation = 'flat'
        surf.actor.property.specular = 0
        surf.actor.property.specular_power = 0
        mlab.contour3d(image_data, contours=10)
        mlab.view(azimuth=azimuth, elevation=elevation, distance='auto')
        mlab.savefig(f"3d_image_{view_name}.png", magnification=2)
        mlab.close()

def calculate_volumes(image_path, image_data):
    nii_img = load_nii_file(image_path)
    if nii_img is not None:
        original_image_data = nii_img.get_fdata()
        voxel_dims = nii_img.header.get_zooms()
        voxel_volume = np.prod(voxel_dims)
        brain_volume_voxels = np.sum(original_image_data > 0)
        brain_volume = brain_volume_voxels * voxel_volume
    else:
        voxel_volume = 1  # Default voxel volume to avoid reference error
        brain_volume = 0

    vessel_threshold = image_data.min() + 0.1 * (image_data.max() - image_data.min())
    vessel_volume_voxels = np.sum(image_data > vessel_threshold)
    vessel_volume = vessel_volume_voxels * voxel_volume
    
    return vessel_volume, brain_volume

def create_pdf_with_3d_slices(vessel_volume, brain_volume, pdf_filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, text="Damar Hacmi / Beyin Hacmi Orani", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(200, 10, text=f"Damar Hacmi: {vessel_volume:.2f} mm^3", align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(200, 10, text=f"Beyin Hacmi: {brain_volume:.2f} mm^3", align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(200, 10, text=f"Hacim Orani: {vessel_volume / (brain_volume + 1e-5):.4f}", align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    angles = ['On', 'Yan', 'Ust']
    for i, view_name in enumerate(angles, start=1):
        if i == 1:
            pdf.cell(200, 10, text=f"3B Görüntü {view_name}", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.image(f"3d_image_{view_name}.png", x=10, y=pdf.get_y() + 10, w=180)
        else:
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)
            pdf.cell(200, 10, text=f"3B Görüntü {view_name}", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.image(f"3d_image_{view_name}.png", x=10, y=pdf.get_y() + 10, w=180)
        os.remove(f"3d_image_{view_name}.png")
    pdf.output(pdf_filename)

def get_image(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Dosya bulunamadı: {image_path}")
    
    img_data, dimensions = None, None
    try:
        img = nib.load(image_path)
        img_data = img.get_fdata()
        dimensions = img_data.shape
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
    
    return img_data, dimensions

def slice_3d_image_axial(img_data, name, dimensions):
    folder_name = "test_png"
    os.makedirs(folder_name, exist_ok=True)
    index = 0
    for slice_index in range(dimensions[2]):
        axial_slice = np.transpose(img_data[:, :, slice_index])
        slice_index_str = str(index).zfill(3)
        axial_slice_image = Image.fromarray(axial_slice.astype("uint8"))
        save_path = os.path.join(folder_name, f"{name}{slice_index_str}.png")
        axial_slice_image.save(save_path)
        index += 1

def output(model_path, output_path):
    tempdir_img = "./test_png"
    tempdir_label = "./test_png"

    testimages = sorted(glob(os.path.join(tempdir_img, "*.png")))
    testsegs = sorted(glob(os.path.join(tempdir_label, "*.png")))

    imtrans = Compose(
        [LoadImage(image_only=True, ensure_channel_first=True), ScaleIntensity()]
    )
    segtrans = Compose(
        [LoadImage(image_only=True, ensure_channel_first=True), ScaleIntensity()]
    )
    val_ds = ArrayDataset(testimages, imtrans, testsegs, segtrans)
    val_loader = DataLoader(
        val_ds, batch_size=1, num_workers=1, pin_memory=torch.cuda.is_available()
    )
    post_trans = Compose([Activations(sigmoid=True), AsDiscrete(threshold=0.5)])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = monai.networks.nets.UNet(
        spatial_dims=2,
        in_channels=1,
        out_channels=1,
        channels=(16, 32, 64, 128, 256),
        strides=(2, 2, 2, 2),
        num_res_units=8,
    ).to(device)
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict(state_dict)

    model.eval()
    with torch.no_grad():
        axial_slices = []
        for val_data in val_loader:
            val_images = val_data[0].to(device)
            roi_size = (96, 96)
            sw_batch_size = 4
            val_outputs = sliding_window_inference(
                val_images, roi_size, sw_batch_size, model
            )
            val_outputs = [post_trans(i) for i in decollate_batch(val_outputs)]
            axial_tensor = val_outputs[0][0]
            axial_slices.append(axial_tensor)

        stacked_tensor = torch.stack(axial_slices, dim=0).squeeze(1)
        output_tensor = stacked_tensor.permute(2, 1, 0)
        numpy_array = output_tensor.cpu().numpy()
        output_tensor_nii = nib.Nifti1Image(numpy_array, affine=np.eye(4))
        nib.save(output_tensor_nii, output_path)
        return output_path

def main(image_path, model_path, output_path, pdf_output_path):
    try:
        img_data, dimensions = get_image(image_path)
        slice_3d_image_axial(img_data, "img", dimensions)
        result = output(model_path, output_path)
        nii_img = load_nii_file(output_path)
        if nii_img is not None:
            image_data = nii_img.get_fdata()
            vessel_volume, brain_volume = calculate_volumes(image_path, image_data)
            plot_and_save_3d(image_data)
            create_pdf_with_3d_slices(vessel_volume, brain_volume, pdf_output_path)
        return result, pdf_output_path
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        print("Usage: python model.py <image_path> <model_path> <output_path> <pdf_output_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    model_path = sys.argv[2]
    output_path = sys.argv[3]
    pdf_output_path = sys.argv[4]

    output_path, pdf_output_filename = main(image_path, model_path, output_path, pdf_output_path)
