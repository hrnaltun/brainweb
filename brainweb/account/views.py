from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.models import User
from guest.models import Servis
from .forms import EmailAuthenticationForm
from django.utils import timezone
from .models import UploadedFile
from .tasks import process_uploaded_file
import uuid
import os


def register_request(request):
    if request.method == 'POST':
        # POST isteğinde kullanıcı bilgilerinin alınması
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email') 
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Şifrelerin eşleşip eşleşmediğini kontrol et
        if password != password_confirm:
            return render(request, 'register.html', {'error': 'Şifreler eşleşmiyor'})

        # Kullanıcıyı oluştur
        user = User.objects.create_user(username=email, email=email, password=password)
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        
        # Kullanıcıyı giriş yap
        return redirect('login')  # Kullanıcıyı giriş sayfasına yönlendir
    else:
        return render(request, 'account/register.html')


def login_request(request):
    servisler = Servis.objects.filter(aktif_pasif=True).order_by("sayfadaki_sırası")
    if request.method == 'POST':
        # POST isteğinde kimlik doğrulama formunu işleme
        form = EmailAuthenticationForm(request.POST)

        if form.is_valid():  # Formun geçerliliğini kontrol et
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:  # Kullanıcı doğrulama başarılıysa
                login(request, user)  # Oturum aç
                return render(request, "account/submit.html", {"servisler": servisler})
            else:
                # Kullanıcı doğrulama başarısızsa hata mesajı gönder
                error = "Kullanıcı adı veya şifre yanlış."
                return render(request, 'account/login.html', {'form': form, 'error': error})
        else:
            # Form geçerli değilse hata mesajı gönder
            error = "Geçersiz form."
            return render(request, 'account/login.html', {'form': form, 'error': error})
    else:
        form = EmailAuthenticationForm()  # GET isteğinde yeni form oluştur
    return render(request, 'account/login.html', {'form': form})


def logout_request(request):
    logout(request)  # Oturum kapat
    return redirect('login')  # Login sayfasına yönlendir

def forgot_request(request):
    return render(request, "account/forgot.html")  # Unutulan şifre sayfasını göster


@login_required
def profile(request):
    # Kullanıcının adı, soyadı ve email bilgilerini almak için request.user kullanılır
    user = request.user
    context = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
    }
    return render(request, 'account/profile.html', context)


@login_required
def account_index(request):
    # Tüm servisleri sayfa sırasına göre al
    servisler = Servis.objects.filter(aktif_pasif=True).order_by('sayfadaki_sırası')
    return render(request, 'account/accountindex.html', {'servisler': servisler})


@login_required
def account_detail_page(request, servis_id):
    # Belirtilen servis kimliğine göre nesneyi al
    servis = get_object_or_404(Servis, id=servis_id)
    return render(request, 'account/accountdetail.html', {'servis': servis})


@login_required
def update_profile(request):
    if request.method == 'POST':
        # POST isteğinde yeni profil bilgilerini al
        email = request.POST.get('email')
        first_name = request.POST.get('fname')
        last_name = request.POST.get('lname')
        
        # Kullanıcının profil bilgilerini güncelle
        user = request.user
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        # Başarı mesajı göster
        messages.success(request, 'Profil başarıyla güncellendi.')
        return redirect('profile')  # Profil sayfasına yönlendir

    return render(request, 'profile_edit.html')  # Profil düzenleme sayfasını göster


@login_required
def change_password(request):
    if request.method == "POST":
        new_password = request.POST.get('newPassword')
        confirm_password = request.POST.get('confirmPassword')

        if new_password == confirm_password:
            # Şifreler eşleştiğinde kullanıcının şifresini değiştir
            user = request.user
            user.set_password(new_password)
            user.save()

            # Şifre değiştirildikten sonra başarı mesajı göster
            messages.success(request, "Şifre başarıyla değiştirildi.")
            logout(request)  # Oturum kapat
            return redirect(reverse('login'))  # Login sayfasına yönlendir

        else:
            # Şifreler eşleşmiyorsa hata mesajı göster
            messages.error(request, "Şifreler eşleşmiyor. Lütfen tekrar deneyin.")

    return render(request, 'account/profile.html')  # Profil sayfasını göster


@login_required
def delete_account(request):
    if request.method == "POST":
        email = request.POST.get('deleteEmail')
        password = request.POST.get('deletePassword')

        # Kullanıcıyı kimlik doğrulama ile kontrol et
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Kullanıcı doğrulandıysa hesabı sil
            user.delete()
            messages.success(request, "Hesabınız başarıyla silindi.")
            return redirect(reverse('login'))   # Login sayfasına yönlendir
        else:
            # Kimlik doğrulama başarısız olduysa hata mesajı göster
            messages.error(request, "E-posta veya şifre yanlış.")

    return render(request, 'account/profile.html')  # Hesabı silme formunu yeniden göster

@login_required
def submit_page(request):
    # Tüm servisleri sayfa sırasına göre al
    servisler = Servis.objects.filter(aktif_pasif=True).order_by('sayfadaki_sırası')
    return render(request, 'account/submit.html', {'servisler': servisler})

@login_required
def get_service_detail(request, service_id):
    # Belirtilen servis kimliğine göre nesneyi alın
    servis = get_object_or_404(Servis, id=service_id)

    # Verileri JSON formatında döndürün
    data = {
        'adı': servis.adı,
        'açıklama': servis.açıklama_kısa,
        'resim': servis.resim.url if hasattr(servis, 'resim') and servis.resim else None,
    }
    return JsonResponse(data)  # JSON formatında yanıt döndürün

@login_required
def upload_file_view(request):
    servisler = Servis.objects.filter(aktif_pasif=True).order_by("sayfadaki_sırası")

    if request.method == "POST":
        uploaded_file = request.FILES.get("file")
        servis_id = request.POST.get("servis_id")

        if not uploaded_file:
            messages.error(request, "Dosya seçilmedi.")
            return render(request, "account/submit.html", {"servisler": servisler})

        # İlk başta UploadedFile nesnesini oluştur ve benzersiz bir ad ver
        unique_id = uuid.uuid4()
        original_filename = uploaded_file.name
        file_extension = os.path.splitext(original_filename)[1]
        
        # Dosya uzantısını kontrol et
        if file_extension not in [".nii", ".gz", ".mha"]:
            messages.error(request, "Dosya uzantısı doğru değil. Lütfen .nii, .nii.gz veya .mha dosyası yükleyin.")
            return render(request, "account/submit.html", {"servisler": servisler})

        # Yeni dosya adını uzantıya göre belirle
        if file_extension == ".mha":
            new_file_name = f"{str(unique_id)[:4]}.mha"  # .mha dosyaları orijinal adını korur
        else:
            new_file_name = f"{str(unique_id)[:4]}.nii.gz"  # Diğerleri benzersiz ad alır

        new_uploaded_file = UploadedFile(
            user=request.user,
            file=uploaded_file,
            upload_date=timezone.now(),
            processing_status="İşleniyor",
        )
        new_uploaded_file.file.name = new_file_name
        new_uploaded_file.save()

        # Dosya yolunu kontrol et
        file_path = new_uploaded_file.file.path
        if not os.path.exists(file_path):
            new_uploaded_file.processing_status = "Başarısız"
            new_uploaded_file.save()
            messages.error(request, "Dosya yolu geçerli değil")
            return render(request, "account/submit.html", {"servisler": servisler})

        # Eğer dosya geçerli ve mevcutsa, Celery görevini tetikle
        process_uploaded_file.delay(new_uploaded_file.id, servis_id)

        messages.success(request, f"Dosya '{new_file_name}' başarıyla yüklendi. Sonuçlar sayfasından görebilirsiniz.")
        return render(request, "account/submit.html", {"servisler": servisler})

    # GET istekleri için veri döndür
    return render(request, "account/submit.html", {"servisler": servisler})

@login_required
def joblist(request):
    # Mevcut kullanıcının UploadedFile nesnelerini al
    user_jobs = UploadedFile.objects.filter(user=request.user)  # Kullanıcıya ait işler
    context = {
        'user_jobs': user_jobs,  # Şablona gönderilecek veriler
    }
    return render(request, "account/joblist.html", context)  # Şablonu ve verileri göster