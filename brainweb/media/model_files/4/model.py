import SimpleITK as sitk
import numpy as np
from mayavi import mlab
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from django.conf import settings
import os
from PIL import Image

def read_and_process_nifti(image_path, output_path):
    # Read the input file
    nesne = sitk.ReadImage(image_path)

    # Convert to numpy array and normalize to 0-1
    nesne_array = sitk.GetArrayFromImage(nesne)
    nesne_array = (nesne_array > 0).astype(float)
    nesne = sitk.GetImageFromArray(nesne_array)
    nesne.CopyInformation(sitk.ReadImage(image_path))

    # Convert the object to 8-bit unsigned integer
    nesne = sitk.Cast(nesne, sitk.sitkUInt8)

    # Calculate MedialSurface using BinaryThinningImageFilter
    medial_surface_filter = sitk.BinaryThinningImageFilter()
    medial_surface = medial_surface_filter.Execute(nesne)

    # Apply DanielssonDistanceMapImageFilter to obtain Daniel map
    danielsson_filter = sitk.DanielssonDistanceMapImageFilter()
    daniel = danielsson_filter.Execute(medial_surface)
    daniel = sitk.Cast(daniel, sitk.sitkFloat32)

    # Convert the object to 32-bit float
    nesne = sitk.Cast(nesne, sitk.sitkFloat32)

    # Multiply Daniel by 2
    daniel = sitk.Multiply(daniel, 2.0)

    # Multiply Daniel with the object to get the result
    sonuc = sitk.Multiply(daniel, nesne)

    # Save the result as .nii.gz file
    sitk.WriteImage(sonuc, output_path)
    print(f'Sonuç dosyası {output_path} olarak kaydedildi.')

    return nesne_array, sonuc

def generate_3d_visualizations(nesne_array, sonuc, output_dir):
    # Convert the result to numpy array for 3D visualization
    sonuc_array = sitk.GetArrayFromImage(sonuc)
    nesne_array = nesne_array.astype(float)  # Ensure nesne_array is float
    
    # Downsample or reduce the size of the arrays if possible
    nesne_array_downsampled = nesne_array[::2, ::2, ::2]
    sonuc_array_downsampled = sonuc_array[::2, ::2, ::2]

    # Get voxel coordinates and thickness values for non-zero elements
    x, y, z = np.nonzero(nesne_array_downsampled)
    thickness_values = sonuc_array_downsampled[x, y, z]

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Generate and save 3D visualizations from different angles
    angles = [(105, 90, 'On', 200), (180, 15, 'Yan', 'auto'), (180, 270, 'Ust', 'auto')]  # Face, side, and top views
    for azimuth, elevation, view_name, distance in angles:
        fig = mlab.figure(size=(1000, 800), bgcolor=(1, 1, 1))  # Set background color to white
        scatter = mlab.points3d(x, y, z, thickness_values, scale_mode='none', scale_factor=1, colormap='viridis')
        mlab.view(azimuth=azimuth, elevation=elevation, distance=distance)
        
        if view_name == 'On':
            colorbar = mlab.colorbar(title='Thickness (mm)', orientation='horizontal')
            colorbar.scalar_bar.unconstrained_font_size = True
            colorbar.scalar_bar.title_text_property.color = (0, 0, 0)  # Set title color to black
            colorbar.scalar_bar.label_text_property.color = (0, 0, 0)  # Set label color to black
            colorbar.scalar_bar_representation.position = [0.1, 0.01]  # Adjust position of the colorbar
            colorbar.scalar_bar_representation.position2 = [0.8, 0.1]  # Adjust size of the colorbar
        else:
            colorbar = mlab.colorbar(title='Thickness (mm)', orientation='vertical')
            colorbar.scalar_bar.title_text_property.color = (0, 0, 0)  # Set title color to black
            colorbar.scalar_bar.label_text_property.color = (0, 0, 0)  # Set label color to black
        
        mlab.savefig(f"{output_dir}/thickness_map_{view_name}.png")
        mlab.close()

def create_pdf_with_3d_slices(output_dir, pdf_output_path):
    pdf = FPDF()

    for view_name in ['On', 'Yan', 'Ust']:
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(200, 10, text=f"3B Görüntü {view_name}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        
        img_path = f"{output_dir}/thickness_map_{view_name}.png"
        if view_name == 'On':
            # Open the image and rotate it
            img = Image.open(img_path)
            img = img.rotate(270, expand=True)
            rotated_img_path = f"{output_dir}/rotated_thickness_map_{view_name}.png"
            img.save(rotated_img_path)
            pdf.image(rotated_img_path, x=10, y=pdf.get_y() + 10, w=180)
            # Optionally remove the rotated image file after adding to PDF
            os.remove(rotated_img_path)
        else:
            pdf.image(img_path, x=10, y=pdf.get_y() + 10, w=180)
        
        # Optionally remove the original PNG files after adding to PDF
        os.remove(img_path)

    pdf.output(pdf_output_path)
    print(f"PDF saved as {pdf_output_path}")

def main(image_path, output_path, pdf_output_path):
    # Define file paths
    output_dir = settings.BASE_DIR

    # Read and process NIfTI file
    nesne_array, sonuc = read_and_process_nifti(image_path, output_path)

    # Generate 3D visualizations
    generate_3d_visualizations(nesne_array, sonuc, output_dir)

    # Create PDF with 3D visualizations
    create_pdf_with_3d_slices(output_dir, pdf_output_path)
    return output_path,pdf_output_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python model.py <image_path> <output_path> <pdf_output_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    output_path = sys.argv[2]
    pdf_output_path = sys.argv[3]

    main(image_path, output_path, pdf_output_path)
