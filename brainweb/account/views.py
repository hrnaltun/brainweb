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
from django.core.paginator import Paginator
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


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
                messages.error(request, "Kullanıcı adı veya şifre yanlış.")
                return render(request, 'account/login.html')
        else:
            # Form geçerli değilse hata mesajı gönder
            messages.error(request, "Geçersiz form.")
            return render(request, 'account/login.html')
    else:
        form = EmailAuthenticationForm()  # GET isteğinde yeni form oluştur
    return render(request, 'account/login.html', {'form': form})


def logout_request(request):
    logout(request)  # Oturum kapat
    return redirect('login')  # Login sayfasına yönlendir

def forgot_request(request):
    if request.method == 'POST':
        email = request.POST.get('mail')
        user = User.objects.filter(email=email).first()
        if user:
            subject = "Şifre Sıfırlama Talebi"
            email_template_name = "account/password_reset_email.html"
            if settings.DEBUG:
                domain = 'localhost:8000'  # Yerel geliştirme için localhost
            else:
                domain = 'beyin.inonu.edu.tr'  # Production ortamı için gerçek domain

            c = {
                "email": user.email,
                'domain': domain,
                'site_name': 'Your Site',
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                'token': default_token_generator.make_token(user),
                'protocol': 'http' if settings.DEBUG else 'https',  # DEBUG moduna göre protokol seçimi
            }
            email_content = render_to_string(email_template_name, c)
            try:
                send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], html_message=email_content)
            except Exception as e:
                messages.error(request, f'E-posta gönderilirken hata oluştu: {e}')
                return redirect('forgot')
            messages.success(request, 'Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.')
            return redirect('login')
        else:
            messages.error(request, 'Bu e-posta adresine kayıtlı bir kullanıcı bulunamadı.')
            return redirect('forgot')

    return render(request, "account/forgot.html")


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            if password == password_confirm:
                user.set_password(password)
                user.save()
                messages.success(request, 'Şifreniz başarıyla güncellendi. Giriş yapabilirsiniz.')
                return redirect('login')
            else:
                messages.error(request, 'Şifreler uyuşmuyor. Lütfen tekrar deneyin.')
        return render(request, 'account/password_reset_confirm.html')
    else:
        messages.error(request, 'Şifre sıfırlama bağlantısı geçersiz.')
        return redirect('forgot')

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

        unique_id = uuid.uuid4()
        original_filename = uploaded_file.name
        
        # Handling the special case for '.nii.gz'
        if original_filename.endswith('.nii.gz'):
            file_without_extension = original_filename[:-7]  # Remove .nii.gz
            file_extension = '.nii.gz'
        else:
            file_without_extension, file_extension = os.path.splitext(original_filename)

        if file_extension not in [".nii", ".gz", ".mha", ".nii.gz"]:
            messages.error(request, "Dosya uzantısı doğru değil. Lütfen .nii, .nii.gz veya .mha dosyası yükleyin.")
            return render(request, "account/submit.html", {"servisler": servisler})

        # Check if the file name already exists in the database
        existing_file = UploadedFile.objects.filter(file__icontains=original_filename).first()
        if existing_file:
            new_file_name = f"{file_without_extension}_{str(unique_id)[:3]}{file_extension}"
        else:
            new_file_name = f"{file_without_extension}_{str(unique_id)[:3]}{file_extension}"

        new_uploaded_file = UploadedFile(
            user=request.user,
            file=uploaded_file,
            upload_date=timezone.now(),
            processing_status="İşleniyor",
        )
        new_uploaded_file.file.name = new_file_name
        new_uploaded_file.save()

        file_path = new_uploaded_file.file.path
        if not os.path.exists(file_path):
            new_uploaded_file.processing_status = "Başarısız"
            new_uploaded_file.save()
            messages.error(request, "Dosya yolu geçerli değil")
            return render(request, "account/submit.html", {"servisler": servisler})

        process_uploaded_file.delay(new_uploaded_file.id, servis_id)

        messages.success(request, f"Dosya '{new_file_name}' başarıyla yüklendi. Sonuçlar sayfasından görebilirsiniz.")
        return render(request, "account/submit.html", {"servisler": servisler})

    return render(request, "account/submit.html", {"servisler": servisler})

@login_required
def joblist(request):
    # Mevcut kullanıcının UploadedFile nesnelerini al ve ID'ye göre azalan sırada sırala
    user_jobs = UploadedFile.objects.filter(user=request.user).order_by('-id')
    
    # Paginator ile sayfalama ekleme
    paginator = Paginator(user_jobs, 10)  # Her sayfada 10 iş listelenecek
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,  # Şablona gönderilecek veriler
    }
    return render(request, "account/joblist.html", context)  # Şablonu ve verileri göster