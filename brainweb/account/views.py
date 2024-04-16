
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate,login
from django.contrib.auth.models import User
from .forms import EmailAuthenticationForm
from django.contrib.auth.decorators import login_required

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
                error = "E-posta adresi veya şifre hatalı."
                return render(request, 'account/register.html', {'form': form, 'error': error})
    else:
        form = EmailAuthenticationForm()
    return render(request,"account/login.html")

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