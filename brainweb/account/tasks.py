from celery import shared_task
from .models import UploadedFile
from guest.models import Servis
import os
import importlib
from django.conf import settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@shared_task
def process_uploaded_file(uploaded_file_id, servis_id):
    uploaded_file_obj = UploadedFile.objects.get(id=uploaded_file_id)
    file_path = uploaded_file_obj.file.path

    # Get the Servis object to check if PDF generation is required
    try:
        servis = Servis.objects.get(id=servis_id)
    except Servis.DoesNotExist:
        uploaded_file_obj.processing_status = "Başarısız"
        uploaded_file_obj.save()
        return f"Servis bulunamadı: {servis_id}"

    # Determine the model path based on servis_id
    model_dir = os.path.join(BASE_DIR, 'media', 'model_files', str(servis_id))
    model_path = os.path.join(model_dir, 'model.pth')

    filename_without_extension = os.path.splitext(uploaded_file_obj.file.name)[0]
    output_filename = f"{filename_without_extension}_output.nii.gz"
    output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', output_filename)

    # Dynamically import the module and call the main function
    module_path = f"media.model_files.{servis_id}.model"
    try:
        model_module = importlib.import_module(module_path)
        if servis.pdf_oluştur:
            pdf_output_filename = f"{filename_without_extension}_output.pdf"
            pdf_output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', pdf_output_filename)

            if os.path.exists(model_path):
                result, result_pdf = model_module.main(file_path, model_path, output_path, pdf_output_path)
            else:
                result, result_pdf = model_module.main(file_path, output_path, pdf_output_path)

        else:

            if os.path.exists(model_path):
                result = model_module.main(file_path, model_path, output_path)
            else:
                result = model_module.main(file_path, output_path)

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

    # Check if the result path exists
    if result and os.path.exists(result):
        uploaded_file_obj.output = result
        uploaded_file_obj.processing_status = "Tamamlandı"
        if servis.pdf_oluştur and result_pdf and os.path.exists(result_pdf):
            uploaded_file_obj.output_pdf = result_pdf
        uploaded_file_obj.save()
        return "Görev başarıyla tamamlandı"
    else:
        uploaded_file_obj.processing_status = "Başarısız"
        uploaded_file_obj.save()
        return f"Çıktı üretilemedi, dosya bulunamadı: {result}"
