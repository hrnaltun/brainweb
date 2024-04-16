from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request,'guest/index.html')
def login_page(request):
    return render(request,'account/login.html')
def service_page(request):
    return render(request,'guest/service.html')