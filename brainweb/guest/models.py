import os
from shutil import rmtree
from django.db import models
from django.conf import settings

def get_upload_path(instance, filename):
    return os.path.join('model_files', str(instance.pk), filename)

class Servis(models.Model):
    adı = models.CharField(max_length=100)
    resim_kücük = models.ImageField(upload_to='hizmet_resimleri/kucuk/')
    açıklama_kısa = models.TextField()
    resim_büyük = models.ImageField(upload_to='hizmet_resimleri/buyuk/')
    açıklama_uzun = models.TextField()
    sayfadaki_sırası = models.IntegerField()
    aktif_pasif = models.BooleanField(default=True)
    model_py_dosyası = models.FileField(upload_to=get_upload_path, default='', blank=True, null=True)  # Model Python dosyasını saklamak için
    model_pth_dosyası = models.FileField(upload_to=get_upload_path, default='', blank=True, null=True)  # Model .pth dosyasını saklamak için
    objects = models.Manager()

    def __str__(self):
        return f"{self.adı}"

    def save(self, *args, **kwargs):
        is_it_new = not bool(self.pk)
        
        if not is_it_new:
            try:
                old_service = Servis.objects.get(id=self.pk)
                old_py_file = old_service.model_py_dosyası.path if old_service.model_py_dosyası else None
                old_pth_file = old_service.model_pth_dosyası.path if old_service.model_pth_dosyası else None

                # Dosyaların değiştirilip değiştirilmediğini kontrol et
                new_py_file = self.model_py_dosyası.file if self.model_py_dosyası else None
                new_pth_file = self.model_pth_dosyası.file if self.model_pth_dosyası else None

                super().save(*args, **kwargs)

                # Eğer model_py_dosyası değiştiyse eski dosyayı sil
                if old_py_file and (not new_py_file or new_py_file.name != old_py_file):
                    try:
                        os.remove(old_py_file)
                    except FileNotFoundError:
                        pass

                # Eğer model_pth_dosyası değiştiyse eski dosyayı sil
                if old_pth_file and (not new_pth_file or new_pth_file.name != old_pth_file):
                    try:
                        os.remove(old_pth_file)
                    except FileNotFoundError:
                        pass

                # Eski dosyalar klasörü boşsa klasörü sil
                old_path = os.path.join(settings.MEDIA_ROOT, 'model_files', str(old_service.pk))
                if os.path.exists(old_path) and not os.listdir(old_path):
                    rmtree(old_path)

                return
            except Servis.DoesNotExist:
                pass

        super().save(*args, **kwargs)
