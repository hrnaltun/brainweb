from celery import shared_task
from .models import UploadedFile
import os
from django.conf import settings
from .mymodels.model1 import get_image, slice_3d_image_axial, output

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@shared_task
def process_uploaded_file(uploaded_file_id):
    
    uploaded_file_obj = UploadedFile.objects.get(id=uploaded_file_id)
    file_path = uploaded_file_obj.file.path
    
    img_data, dimensions = get_image(file_path)
    
    slice_3d_image_axial(img_data, "img", dimensions)

    model_path = os.path.join( BASE_DIR, 'account' , 'mymodels' , 'model_rukiye.pth' )

    if not os.path.exists(model_path):
        uploaded_file_obj.processing_status = "Başarısız"
        uploaded_file_obj.save()
        return "Model dosyası bulunamadı"
    
    filename_without_extension = os.path.splitext(uploaded_file_obj.file.name)[0]
    output_filename = f"{filename_without_extension}_output.nii.gz"
    output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', output_filename)
    
    output_path = output(model_path,output_path)
    
    if output_path:
        uploaded_file_obj.output = output_path
        uploaded_file_obj.processing_status = "Tamamlandı"
        uploaded_file_obj.save()
        return "Görev başarıyla tamamlandı"
    else:
        uploaded_file_obj.processing_status = "Başarısız"
        uploaded_file_obj.save()
        return "Çıktı üretilemedi"