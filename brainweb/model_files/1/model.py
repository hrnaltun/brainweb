import os
from glob import glob
import numpy as np
import monai
import torch
from PIL import Image
import nibabel as nib
from monai.data import ArrayDataset, decollate_batch, DataLoader
from monai.inferers import sliding_window_inference
from monai.metrics import DiceMetric
from monai.transforms import Activations, AsDiscrete, Compose, LoadImage, ScaleIntensity


def get_image(image_path):
    # Dosyanın var olup olmadığını kontrol et
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Dosya bulunamadı: {image_path}")
    
    # Başlangıçta None değerlerini atayın
    img_data = None
    dimensions = None

    try:
        img = nib.load(image_path)  # Resmi yüklemeye çalış
        img_data = img.get_fdata()  # Veri al
        dimensions = img_data.shape  # Boyutları al
    except Exception as e:  # Hata durumunda hata mesajını da yakalayın
        # Hata olursa, img_data ve dimensions None kalır
        print(f"Bir hata oluştu: {e}")
    
    return img_data, dimensions


def slice_3d_image_axial(img_data, name, dimensions):
    folder_name = "test_png"  # Klasör adı
    os.makedirs(folder_name, exist_ok=True)  # Klasörü oluşturun (varsa geçersiz kıl)
    index = 0
    for slice_index in range(dimensions[2]):
        axial_slice = np.transpose(img_data[:, :, slice_index])  # Boyutları döndür
        slice_index_str = str(index).zfill(3)
        # Görüntüyü uygun modda oluşturun (varsayılan olarak 'L' kullanıyoruz)
        axial_slice_image = Image.fromarray(axial_slice.astype("uint8"))
        # Görüntüyü PNG formatında kaydedin
        save_path = os.path.join(folder_name, f"{name}{slice_index_str}.png")
        axial_slice_image.save(save_path)  # Görüntüyü kaydedin
        index += 1

    dimensions = ( dimensions[0], dimensions[1],dimensions[2])


def output(model_path, output_path):
    tempdir_img = "./test_png"
    tempdir_label = "./test_png"

    testimages = sorted(glob(os.path.join(tempdir_img, "*.png")))
    testsegs = sorted(glob(os.path.join(tempdir_label, "*.png")))

    # Görüntü ve segmentasyon için dönüşümleri tanımla
    imtrans = Compose(
        [LoadImage(image_only=True, ensure_channel_first=True), ScaleIntensity()]
    )
    segtrans = Compose(
        [LoadImage(image_only=True, ensure_channel_first=True), ScaleIntensity()]
    )
    val_ds = ArrayDataset(testimages, imtrans, testsegs, segtrans)

    # Veri yükleyicisini oluştur
    val_loader = DataLoader(
        val_ds, batch_size=1, num_workers=1, pin_memory=torch.cuda.is_available()
    )

    # Dice metriğini başlat
    dice_metric = DiceMetric(
        include_background=True, reduction="mean", get_not_nans=False
    )

    # Son işlemler için dönüşümleri tanımla
    post_trans = Compose([Activations(sigmoid=True), AsDiscrete(threshold=0.5)])

    # Aygıtı belirle
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # Modeli başlat
    model = monai.networks.nets.UNet(
        spatial_dims=2,
        in_channels=1,
        out_channels=1,
        channels=(16, 32, 64, 128, 256),
        strides=(2, 2, 2, 2),
        num_res_units=8,
    ).to(device)
    # Önceden eğitilmiş modeli yükle
    state_dict = torch.load(model_path, map_location=torch.device("cpu"))
    model.load_state_dict(state_dict)

    model.eval()
    # Çıkarım yap
    with torch.no_grad():
        axial_slices = []

        for val_data in val_loader:
            val_images = val_data[0].to(device)

            # Pencere kaydırma çıkarımı için pencere boyutu ve grup boyutunu tanımla
            roi_size = (96, 96)
            sw_batch_size = 4
            val_outputs = sliding_window_inference(
                val_images, roi_size, sw_batch_size, model
            )
            val_outputs = [post_trans(i) for i in decollate_batch(val_outputs)]

            # Boyutları değiştirmeyin, orijinal boyutları koruyun
            axial_tensor = val_outputs[0][0]  # (1, H, W)
            axial_slices.append(axial_tensor)

        # Sliceları birleştirerek 3 boyutlu bir tensör oluştur
        stacked_tensor = torch.stack(axial_slices, dim=0).squeeze(1)  # (S, H, W)

        # Boyutları döndürerek output_tensor oluştur
        output_tensor = stacked_tensor.permute(2,1,0)  # Boyutları döndür
        # Kayıt
        numpy_array = output_tensor.cpu().numpy()
        output_tensor_nii = nib.Nifti1Image(numpy_array, affine=np.eye(4))
        # Dosyayı .nii.gz olarak kaydet
        nib.save(output_tensor_nii, output_path)
        return output_path

def main(image_path, model_path, output_path):
    try:
        img_data, dimensions = get_image(image_path)
        slice_3d_image_axial(img_data, "img", dimensions)
        result = output(model_path,output_path)
        return result
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 5:
        print("Usage: python model.py <image_path> <model_path> <output_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    model_path = sys.argv[2]
    output_path = sys.argv[3]

    main(image_path, model_path, output_path)