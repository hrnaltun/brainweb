from django.db import models
from django.conf import settings
from django.utils import timezone

# Kullanıcı tarafından yüklenen dosyaların saklandığı model
class UploadedFile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Dosyanın sahibini belirtir
    file = models.FileField(upload_to='uploads/')  # Dosyanın saklandığı yolu belirtir
    upload_date = models.DateTimeField(default=timezone.now)  # Dosyanın yüklendiği zamanı kaydeder
    processing_status = models.CharField(max_length=50, default='İşleniyor')  # İşleme durumunu tutar
    output = models.FileField(upload_to='outputs/', null=True, blank=True)  # İşlem sonucu PDF dosyası
    objects = models.Manager()
    
    def __str__(self):
        return f"{self.id}"  # Modeli temsil eden metin
