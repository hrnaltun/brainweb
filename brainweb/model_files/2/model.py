import warnings
import os
import numpy as np
import nibabel as nib
import torch
from monai.data import CacheDataset, DataLoader
from monai.inferers import sliding_window_inference
from monai.networks.layers import Norm
from monai.networks.nets import UNet
from monai.transforms import (
    AsDiscrete,
    Compose,
    EnsureChannelFirstd,
    LoadImaged,
    Orientationd,
    ScaleIntensityRanged,
    Spacingd
)
from monai.data.utils import decollate_batch
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
    x, y, z = np.indices(image_data.shape)
    angles = [(90, 90, 'On'), (0, 90, 'Yan'), (0, 0, 'Ust')]

    for i, (azimuth, elevation, view_name) in enumerate(angles, start=1):
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
    # Orijinal NIfTI dosyasını yükleyerek beyin hacmini hesapla
    nii_img = load_nii_file(image_path)
    if nii_img is not None:
        original_image_data = nii_img.get_fdata()
        voxel_dims = nii_img.header.get_zooms()
        voxel_volume = np.prod(voxel_dims)
        brain_volume_voxels = np.sum(original_image_data > 0)
        brain_volume = brain_volume_voxels * voxel_volume
    else:
        brain_volume = 0  # veya uygun bir hata yönetimi yapabilirsiniz

    # Damar hacmini hesapla
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

def main(image_path, model_path, output_path, pdf_output_path):
    warnings.filterwarnings('ignore')
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    
    available_gpus = torch.cuda.device_count()
    device = torch.device("cuda:1" if available_gpus > 1 else "cuda:0" if available_gpus == 1 else "cpu")
    torch.backends.cudnn.benchmark = True

    pixdim = (0.513392984867096, 0.513392984867096, 0.8000029921531677)

    def prepare_data():
        val_files = [{"image": image_path}]
        val_transforms = Compose([
            LoadImaged(keys=["image"]),
            EnsureChannelFirstd(keys=["image"]),
            ScaleIntensityRanged(keys=["image"], a_min=45.0, a_max=230.0, b_min=0.0, b_max=1.0, clip=True),
            Spacingd(keys=["image"], pixdim=pixdim, mode=("bilinear")),
            Orientationd(keys=["image"], axcodes="RAS"),
        ])
        val_ds = CacheDataset(data=val_files, transform=val_transforms, cache_rate=1.0)
        return val_ds

    val_ds = prepare_data()
    val_loader = DataLoader(val_ds, batch_size=1, shuffle=False, pin_memory=True)

    model = UNet(
        spatial_dims=3,
        in_channels=1,
        out_channels=2,
        channels=(16, 32, 64, 128, 256),
        strides=(2, 2, 2, 2),
        num_res_units=2,
        norm=Norm.INSTANCE,
    ).to(device)

    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    with torch.no_grad():
        for val_data in val_loader:
            val_inputs = val_data["image"].to(device)
            roi_size = (96, 96, 96)
            sw_batch_size = 4
            val_outputs = sliding_window_inference(val_inputs, roi_size, sw_batch_size, model)
            val_outputs = [AsDiscrete(argmax=True, to_onehot=2)(i) for i in decollate_batch(val_outputs)]

            val_output_np = val_outputs[0].cpu().numpy()

            output_img = nib.Nifti1Image(val_output_np[1], np.eye(4))
            output_img.header['pixdim'] = [1, 0.513392984867096, 0.513392984867096, 0.8000029921531677, 0, 0, 0, 0]
            nib.save(output_img, output_path)

            nii_img = load_nii_file(output_path)
            if nii_img is not None:
                image_data = nii_img.get_fdata()
                vessel_volume , brain_volume = calculate_volumes(image_path, image_data)
                plot_and_save_3d(image_data)
                create_pdf_with_3d_slices(vessel_volume, brain_volume, pdf_filename=pdf_output_path)
            
            return output_path, pdf_output_path

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
