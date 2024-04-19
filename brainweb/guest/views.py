from django.shortcuts import render,get_object_or_404
from .models import Servis

# Create your views here.
def index(request):
    servisler = Servis.objects.all().order_by('sayfadaki_sırası')
    return render(request, 'guest/index.html', {'servisler': servisler})
def login_page(request):
    return render(request,'account/login.html')
def service_page(request):
    servisler = Servis.objects.all().order_by('sayfadaki_sırası')
    return render(request, 'guest/service.html', {'servisler': servisler})
def service_detail_page(request, servis_id):
    servis = get_object_or_404(Servis, id=servis_id)
    return render(request, 'guest/servicedetail.html', {'servis': servis})