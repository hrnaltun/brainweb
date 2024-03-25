from django.urls import path

from user import views
urlpatterns = [
    path('home/index', views.index),
]