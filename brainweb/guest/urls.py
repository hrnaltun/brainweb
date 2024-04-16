from django.urls import path

from guest import views

urlpatterns = [
    path('', views.index, name='index'),
    path('guest/login', views.login_page, name='login_page'),
]