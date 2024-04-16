from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request,'guest/index.html')



def service_view(request):
    return render(request, 'service.html')




def beyindamar_view(request):
    return render(request, 'guest/beyindamar.html')

def beyintümör_view(request):
    return render(request, 'guest/beyintümör.html')

def kafatasi_view(request):
    return render(request, 'guest/kafatasi.html')

def riskharitasi_view(request):
    return render(request, 'guest/riskharitasi.html')

def stn_view(request):
    return render(request, 'guest/stn.html')

    


