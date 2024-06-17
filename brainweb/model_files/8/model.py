import numpy as np
import nibabel as nib
from scipy import ndimage
from skimage.measure import marching_cubes
from skimage.morphology import binary_opening, binary_closing, cube
import os
from mayavi import mlab
from fpdf import FPDF

def extract_skull_mask(MR):
    # Marching cubes ile yüzey çıkarımı
    verts, faces, _, _ = marching_cubes(MR, level=0.7 * np.mean(MR), spacing=(1.0, 1.0, 1.0))
    
    # Boş bir mask oluştur
    skull_mask = np.zeros(MR.shape, dtype=bool)
    
    # Yüzey noktalarını maske olarak ayarla
    for i, j, k in verts:
        skull_mask[int(i), int(j), int(k)] = True
    
    # Morfolojik işlemler ile küçük nesneleri temizle ve kapatma işlemi yap
    skull_mask = binary_closing(skull_mask, footprint=cube(5))
    skull_mask = binary_opening(skull_mask, footprint=cube(5))
    
    # Yoğunluk eşikleme ile cilt bölgesini kaldır
    high_intensity_mask = MR > np.percentile(MR[skull_mask], 80)
    skull_mask = skull_mask & high_intensity_mask

    return skull_mask

def load_nii_file(file_path):
    try:
        return nib.load(file_path)
    except Exception as e:
        print(f"Error loading NIfTI file: {e}")
        return None

def plot_and_save_3d(image_data):
    angles = [
        (55, 90, 'Sol'),
        (105, 90, 'Sag')
    ]

    for azimuth, elevation, view_name in angles:
        fig = mlab.figure(size=(1000, 800), bgcolor=(1, 1, 1))
        src = mlab.pipeline.scalar_field(image_data.astype(np.uint8))  # Boolean array to uint8
        src.spacing = [1, 1, 1]
        surf = mlab.pipeline.iso_surface(src, opacity=0.5, colormap='inferno')
        surf.actor.property.interpolation = 'flat'
        surf.actor.property.specular = 0
        surf.actor.property.specular_power = 0
        mlab.contour3d(image_data.astype(np.uint8), contours=10)  # Boolean array to uint8
        mlab.view(azimuth=azimuth, elevation=elevation, distance='auto')
        mlab.savefig(f"3d_image_{view_name}.png", magnification=2)
        mlab.close()


def create_pdf_with_3d_slices(pdf_filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    angles = ['Sol', 'Sag']
    for index, view_name in enumerate(angles):
        if index > 0:
            pdf.add_page()  # Add a new page for each view except the first one
        pdf.cell(200, 10, text=f"3B Görüntü {view_name}", align='C', ln=True)
        pdf.image(f"3d_image_{view_name}.png", x=10, y=pdf.get_y() + 10, w=180)
        os.remove(f"3d_image_{view_name}.png")
        pdf.set_font("Helvetica", size=12)
    
    pdf.output(pdf_filename)

def main(image_path, output_path, pdf_output_path):
    # NIfTI dosyasını oku
    img = nib.load(image_path)
    MR = img.get_fdata()

    # Kafatası maskesini elde et
    skull_mask = extract_skull_mask(MR)

    # Sonucu yeni bir NIfTI dosyasına kaydet
    new_img = nib.Nifti1Image(skull_mask.astype(np.uint8), img.affine, img.header)
    nib.save(new_img, output_path)
    
    # 3B görüntüleri kaydet
    plot_and_save_3d(skull_mask)
    
    # PDF oluştur
    create_pdf_with_3d_slices(pdf_output_path)
    return output_path, pdf_output_path
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python model.py <image_path> <output_path> <pdf_output_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    output_path = sys.argv[2]
    pdf_output_path = sys.argv[3]

    main(image_path, output_path, pdf_output_path)
