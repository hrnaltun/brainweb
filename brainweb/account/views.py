
from django.shortcuts import redirect, render,get_object_or_404
from django.contrib.auth import authenticate,login,update_session_auth_hash
from django.contrib.auth.models import User
from .forms import EmailAuthenticationForm
from django.contrib.auth.decorators import login_required
from guest.models import Servis
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse

# Create your views here.
def register_request(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('mail')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
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
    if request.method == 'POST':
        form = EmailAuthenticationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('profile')  
            else:
                error = "Kullanıcı adı veya şifre yanlış."
                return render(request, 'account/login.html', {'form': form, 'error': error})
        else:
            error = "Geçersiz form."
            return render(request, 'account/login.html', {'form': form, 'error': error})
    else:
        form = EmailAuthenticationForm()
    return render(request, 'account/login.html', {'form': form})


def logout_request(request):
    return redirect("index")

def forgot_request(request):
    return render(request,"account/forgot.html")

@login_required
def profile(request):
    # Kullanıcının adı, soyadı ve email bilgilerini almak için request.user kullanabiliriz
    user = request.user
    context = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
    }
    return render(request, 'account/profile.html', context)

@login_required
def account_index(request):
    servisler = Servis.objects.all().order_by('sayfadaki_sırası')
    return render(request, 'account/accountindex.html', {'servisler': servisler})

@login_required
def account_detail_page(request, servis_id):
    servis = get_object_or_404(Servis, id=servis_id)
    return render(request, 'account/accountdetail.html', {'servis': servis})

@login_required
def update_profile(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('fname')
        last_name = request.POST.get('lname')
        
        # Kullanıcının profil bilgilerini güncelle
        user = request.user
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        messages.success(request, 'Profil başarıyla güncellendi.')
        return redirect('profile')  # Profil sayfasına yönlendirme

    return render(request, 'profile_edit.html')  # Profil düzenleme sayfasını göster

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Oturumu güncelle, şifre değiştiği için
            messages.success(request, 'Şifreniz başarıyla güncellendi.')
            return redirect(reverse('profile'))  # profil sayfasına yönlendir
    else:
        form = PasswordChangeForm(user=request.user)
    
    return render(request, 'account/profile.html', {'form': form})