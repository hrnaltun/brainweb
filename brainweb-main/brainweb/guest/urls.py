from django.urls import path

from guest import views

urlpatterns = [
    path('', views.index),
    path('guest/index', views.index),
]