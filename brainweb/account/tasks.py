from celery import shared_task
from .models import UploadedFile
from guest.models import Servis
import os
import importlib
from django.conf import settings

@shared_task
def process_uploaded_file(uploaded_file_id, servis_id):
    try:
        uploaded_file_obj = UploadedFile.objects.get(id=uploaded_file_id)
        servis = Servis.objects.get(id=servis_id)
        file_path = uploaded_file_obj.file.path

        results = []

        if servis.çoklu_servis and servis.çalıştırılacak_servisler:
            # Çalıştırılacak servislerin ID'lerini ayırıp liste haline getir
            run_service_ids = [int(sid.strip()) for sid in servis.çalıştırılacak_servisler.split(',') if sid.strip()]

            for run_servis_id in run_service_ids:
                # Her bir servis için işlem yap
                model_dir = os.path.join(settings.BASE_DIR, 'media', 'model_files', str(run_servis_id))
                model_path = os.path.join(model_dir, 'model.pth')

                filename_without_extension = os.path.splitext(uploaded_file_obj.file.name)[0]
                output_filename = f"{filename_without_extension}_{run_servis_id}_output.nii.gz"
                output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', output_filename)

                module_path = f"media.model_files.{run_servis_id}.model"
                try:
                    model_module = importlib.import_module(module_path)
                    if not hasattr(model_module, 'main'):
                        uploaded_file_obj.processing_status = "Başarısız"
                        uploaded_file_obj.save()
                        return f"Modülde 'main' fonksiyonu bulunamadı: {module_path}"
                    run_servis = Servis.objects.get(id=run_servis_id)
                    if run_servis.pdf_oluştur:
                        print("çalışıyor2")
                        pdf_output_filename = f"{filename_without_extension}_{run_servis_id}_output.pdf"
                        pdf_output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', pdf_output_filename)
                        print("çalışıyor")
                        if os.path.exists(model_path):
                            result, _ = model_module.main(file_path, model_path, output_path, pdf_output_path)
                        else:
                            result, _ = model_module.main(file_path, output_path, pdf_output_path)
                    else:
                        if os.path.exists(model_path):
                            result, _ = model_module.main(file_path, model_path, output_path)
                        else:
                            result, _ = model_module.main(file_path, output_path)

                    results.append(result)

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

                uploaded_file_obj.save()

            model_dir = os.path.join(settings.BASE_DIR, 'media', 'model_files', str(servis_id))
            model_path = os.path.join(model_dir, 'model.pth')

            filename_without_extension = os.path.splitext(uploaded_file_obj.file.name)[0]
            output_filename = f"{filename_without_extension}_output.nii.gz"
            output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', output_filename)
            module_path = f"media.model_files.{servis_id}.model"

            try:
                model_module = importlib.import_module(module_path)
                if not hasattr(model_module, 'main'):
                    uploaded_file_obj.processing_status = "Başarısız"
                    uploaded_file_obj.save()
                    return f"Modülde 'main' fonksiyonu bulunamadı: {module_path}"
                
                if servis.pdf_oluştur:
                    pdf_output_filename = f"{filename_without_extension}_output.pdf"
                    pdf_output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', pdf_output_filename)
                    if os.path.exists(model_path):
                        result, result_pdf = model_module.main(results, model_path, output_path, pdf_output_path)
                    else:
                        result, result_pdf = model_module.main(results, output_path, pdf_output_path)
                else:
                    if os.path.exists(model_path):
                        result = model_module.main(results, model_path, output_path)
                    else:
                        result = model_module.main(results, output_path)

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

            uploaded_file_obj.output = result
            uploaded_file_obj.processing_status = "Tamamlandı"
            if servis.pdf_oluştur and result_pdf and os.path.exists(result_pdf):
                uploaded_file_obj.output_pdf = result_pdf
            uploaded_file_obj.save()
            return "Görev başarıyla tamamlandı"

        else:
            # Normal işlem devam ediyor
            model_dir = os.path.join(settings.BASE_DIR, 'media', 'model_files', str(servis_id))
            model_path = os.path.join(model_dir, 'model.pth')

            filename_without_extension = os.path.splitext(uploaded_file_obj.file.name)[0]
            output_filename = f"{filename_without_extension}_output.nii.gz"
            output_path = os.path.join(settings.MEDIA_ROOT, 'outputs', output_filename)

            module_path = f"media.model_files.{servis_id}.model"
            try:
                model_module = importlib.import_module(module_path)
                if not hasattr(model_module, 'main'):
                    uploaded_file_obj.processing_status = "Başarısız"
                    uploaded_file_obj.save()
                    return f"Modülde 'main' fonksiyonu bulunamadı: {module_path}"
                
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

            # uploaded_file_obj içine sonucu kaydet
            uploaded_file_obj.output = result
            uploaded_file_obj.processing_status = "Tamamlandı"
            if servis.pdf_oluştur and result_pdf and os.path.exists(result_pdf):
                uploaded_file_obj.output_pdf = result_pdf
            uploaded_file_obj.save()
            return "Görev başarıyla tamamlandı"

    except UploadedFile.DoesNotExist:
        return f"Yüklenen dosya bulunamadı: {uploaded_file_id}"
    except Servis.DoesNotExist:
        return f"Servis bulunamadı: {servis_id}"