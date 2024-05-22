import torch
import warnings
import os
import numpy as np
import nibabel as nib
from monai.data import CacheDataset, DataLoader, decollate_batch
from monai.networks.layers import Norm
from monai.inferers import sliding_window_inference
from monai.networks.nets import UNet
from monai.transforms import (
    AsDiscrete,
    Compose,
    CropForegroundd,
    EnsureChannelFirstd,
    LoadImaged,
    Orientationd,
    ScaleIntensityRanged,
    Spacingd,
)

def main(image_path, model_path, output_path):
    # Gerekli kütüphanelerin kurulması
    warnings.filterwarnings('ignore')
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    
    # Check the number of available GPUs
    available_gpus = torch.cuda.device_count()
    if available_gpus > 1:
        device = torch.device("cuda:1")
    elif available_gpus == 1:
        device = torch.device("cuda:0")
    else:
        device = torch.device("cpu")
    
    torch.backends.cudnn.benchmark = True

    # Path and settings
    val_image = image_path

    # Updated function to prepare data without labels
    def prepare_data(image_path):
        val_files = [{"image": image_path}]
        pixdim = (0.513392984867096, 0.513392984867096, 0.8000029921531677)
        val_transforms = Compose(
            [
                LoadImaged(keys=["image"]),
                EnsureChannelFirstd(keys=["image"]),
                ScaleIntensityRanged(
                    keys=["image"],
                    a_min=45.0,
                    a_max=230.0,
                    b_min=0.0,
                    b_max=1.0,
                    clip=True,
                ),
                CropForegroundd(keys=["image"], source_key="image"),
                Orientationd(keys=["image"], axcodes="RAS"),
                Spacingd(
                    keys=["image"],
                    pixdim=pixdim,
                    mode=("bilinear"),
                ),
            ]
        )

        val_ds = CacheDataset(
            data=val_files,
            transform=val_transforms,
            cache_rate=1.0,
        )
        return val_ds

    val_ds = prepare_data(val_image)
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

    # Load model with map_location
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    model.to(device)

    with torch.no_grad():
        val_data = next(iter(val_loader))
        val_inputs = val_data["image"].to(device)
        
        roi_size = (96, 96, 96)
        sw_batch_size = 4
        val_outputs = sliding_window_inference(val_inputs, roi_size, sw_batch_size, model)
        val_outputs = [AsDiscrete(argmax=True, to_onehot=2)(i) for i in decollate_batch(val_outputs)]

        # Assuming post_pred outputs are tensors, convert them to numpy arrays
        val_outputs_np = val_outputs[0].cpu().numpy()

        # Save the output to a NIfTI file
        output_img = nib.Nifti1Image(val_outputs_np[1], np.eye(4))  # use [1] to extract the vessel class
        nib.save(output_img, output_path)
        return output_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python model.py <image_path> <model_path> <output_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    model_path = sys.argv[2]
    output_path = sys.argv[3]

    main(image_path, model_path, output_path)
