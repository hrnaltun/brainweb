import numpy as np
import nibabel as nib
import os
from mayavi import mlab
from fpdf import FPDF
from scipy.ndimage import gaussian_filter

# NIfTI dosyasını okuma ve normalize etme fonksiyonu
def load_and_normalize_nii(file_path):
    img = nib.load(file_path)
    data = img.get_fdata()
    header = img.header
    affine = img.affine
    data = (data - np.min(data)) / (np.max(data) - np.min(data))
    return data, header, affine

# Yeni eşikleme yöntemi ile kafatası çıkarma fonksiyonu
def head_strip_thresholdMuStd(data):    
    # Eşik değerini hesaplama
    threshold = np.mean(data) + 0.1 * np.std(data)
    mask = data > threshold
    return mask

# Sonuçları kaydetme fonksiyonu
def save_nifti(data, file_path, header, affine):
    nifti_img = nib.Nifti1Image(data.astype(np.float32), affine, header)
    nib.save(nifti_img, file_path)

def plot_and_save_3d(image_data):
    angles = [
        (90, 90, 'On'),   
        (0, 90, 'Sol'),
        (0, 0, 'Ust')
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
    
    angles = [ 'On','Sol', 'Ust']
    for index, view_name in enumerate(angles):
        if index > 0:
            pdf.add_page()  # Add a new page for each view except the first one
        pdf.cell(200, 10, text=f"3B Görüntü {view_name}", align='C', ln=True)
        pdf.image(f"3d_image_{view_name}.png", x=10, y=pdf.get_y() + 10, w=180)
        os.remove(f"3d_image_{view_name}.png")
        pdf.set_font("Helvetica", size=12)
    
    pdf.output(pdf_filename)

def main(image_path, output_path, pdf_output_path):
    # NIfTI dosyasının var olup olmadığını kontrol et
    if os.path.exists(image_path):
        data, header, affine = load_and_normalize_nii(image_path)

        # Yumuşatma işlemi
        data = gaussian_filter(data, sigma=1)
        
        # Yeni eşikleme yöntemi ile kafatası çıkarma
        head_thresholdMuStd = head_strip_thresholdMuStd(data)
        
        # MuStd eşikleme sonucunu kaydetme
        save_nifti(head_thresholdMuStd, output_path, header, affine)

        # 3B görüntüleri kaydet
        plot_and_save_3d(head_thresholdMuStd)
        
        # PDF oluştur
        create_pdf_with_3d_slices(pdf_output_path)
        return output_path, pdf_output_path
    else:
        print(f"Dosya bulunamadı: {image_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python model.py <image_path> <output_path> <pdf_output_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    output_path = sys.argv[2]
    pdf_output_path = sys.argv[3]

    main(image_path, output_path, pdf_output_path)
