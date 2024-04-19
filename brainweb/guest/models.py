from django.db import models

# Create your models here.

class Servis(models.Model):
    adı = models.CharField(max_length=100)
    resim_kücük = models.ImageField(upload_to='hizmet_resimleri/kucuk/')
    açıklama_kısa = models.TextField()
    resim_büyük = models.ImageField(upload_to='hizmet_resimleri/buyuk/')
    açıklama_uzun = models.TextField()
    sayfadaki_sırası = models.IntegerField()
    aktif_pasif = models.BooleanField(default=True)
    objects = models.Manager()

    def __str__(self):
        return f"{self.adı}"