"""
URL configuration for brainweb project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from guest import views

urlpatterns = [
   path('admin/', admin.site.urls),
    path('', views.index, name='home'),  # Ana sayfaya yönlendirme yapar
    path('service/', views.service_view, name='service'),
    path('guest/', include('guest.urls')),  # guest uygulamasının URL'lerini içeri alır
    path('user/', include('user.urls')),    # user uygulamasının URL'lerini içeri alır
    
    path('beyintümör/', views.beyintümör_view, name='beyintümör'),
    path('beyindamar/', views.beyindamar_view, name='beyindamar'),
    path('kafatasi/', views.kafatasi_view, name='kafatasi'),
    path('riskharitasi/', views.riskharitasi_view, name='riskharitasi'),
    path('stn/', views.stn_view, name='stn'),
]
    
    
    
    
    

