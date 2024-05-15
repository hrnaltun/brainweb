from celery import shared_task
from .models import UploadedFile
import os
import importlib
from django.conf import settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@shared_task
def process_uploaded_file(uploaded_file_id, servis_id):
    uploaded_file_obj = UploadedFile.objects.get(id=uploaded_file_id)
    file_path = uploaded_file_obj.file.path

    # Determine the model path based on servis_id
    model_dir = os.path.join(BASE_DIR, 'model_files', str(servis_id))
    model_path = os.path.join(model_dir, 'model.pth')


    if not os.path.exists(model_path):
        print(f"servis id: {servis_id}")
        uploaded_file_obj.processing_status = "Başarısız"
        uploaded_file_obj.save()
        return print(f"Model directory: {model_dir}")

    filename_without_extension = os.path.splitext(uploaded_file_obj.file.name)[0]
    output_filename = f"{filename_without_extension}_output.nii.gz"
    output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', output_filename)

    # Dynamically import the module and call the main function
    module_path = f"model_files.{servis_id}.model"
    try:
        model_module = importlib.import_module(module_path)
        result = model_module.main(file_path, model_path, output_path)
    except ModuleNotFoundError:
        uploaded_file_obj.processing_status = "Başarısız"
        uploaded_file_obj.save()
        return f"Model modülü bulunamadı: {module_path}"
    except AttributeError:
        uploaded_file_obj.processing_status = "Başarısız"
        uploaded_file_obj.save()
        return f"Modülde 'main' fonksiyonu bulunamadı: {module_path}"
    except Exception as e:
        uploaded_file_obj.processing_status = "Başarısız"
        uploaded_file_obj.save()
        return f"Bir hata oluştu: {str(e)}"

    if result:
        uploaded_file_obj.output = output_path
        uploaded_file_obj.processing_status = "Tamamlandı"
        uploaded_file_obj.save()
        return "Görev başarıyla tamamlandı"
    else:
        uploaded_file_obj.processing_status = "Başarısız"
        uploaded_file_obj.save()
        return "Çıktı üretilemedi"
