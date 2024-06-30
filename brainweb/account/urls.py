from django.urls import path, include
from django.views.i18n import set_language
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='home'),

    path('login/', views.login_request, name='login'),
    path('register/', views.register_request, name='register'),
    path('logout/', views.logout_request, name='logout'),
    path('forgot/', views.forgot_request, name='forgot'),
    path('profile/', views.profile, name='profile'),
    path('homepage/', views.account_index, name='index_account'),
    path('account/servicedetail/<int:servis_id>/', views.account_detail_page, name='account_detail_page'),
    path('profile/edit/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/delete-account/', views.delete_account, name='delete_account'),
    path('submit/', views.submit_page, name='submit_page'),
    path('service/<int:service_id>/', views.get_service_detail, name='service_detail'),
    path('joblist/', views.joblist, name='joblist'),
    path('upload/', views.upload_file_view, name='upload_file'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('set-language/', set_language, name='set_language'),

    # Dil değiştirme sonrası yönlendirme için URL patternleri
    path('<str:language_code>/', include([
        path('login/', views.login_request, name='login'),
        path('register/', views.register_request, name='register'),
        path('logout/', views.logout_request, name='logout'),
        path('forgot/', views.forgot_request, name='forgot'),
        path('profile/', views.profile, name='profile'),
        path('homepage/', views.account_index, name='index_account'),
        path('account/servicedetail/<int:servis_id>/', views.account_detail_page, name='account_detail_page'),
        path('profile/edit/', views.update_profile, name='update_profile'),
        path('profile/change-password/', views.change_password, name='change_password'),
        path('profile/delete-account/', views.delete_account, name='delete_account'),
        path('submit/', views.submit_page, name='submit_page'),
        path('service/<int:service_id>/', views.get_service_detail, name='service_detail'),
        path('joblist/', views.joblist, name='joblist'),
        path('upload/', views.upload_file_view, name='upload_file'),
        path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    ])),
]

