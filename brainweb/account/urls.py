from django.urls import path

from . import views

urlpatterns = [
    path('login', views.login_request, name='login'),
    path('register', views.register_request, name='register'),
    path('logout', views.logout_request, name='logout'),
    path('forgot', views.forgot_request, name='forgot'),
    path('profile', views.profile, name='profile'),
    path('homepage', views.account_index, name='index_account'),
    path('account/servicedetail/<int:servis_id>/', views.account_detail_page, name='account_detail_page'),
    path('profile/edit/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/delete-account/', views.delete_account, name='delete_account'),
    path('account/submit', views.submit_page, name='submit_page'),
    path('service/<int:service_id>/', views.get_service_detail, name='service_detail'),
    path('joblist',views.joblist,name="joblist"),
    path('upload/', views.upload_file_view, name='upload_file'),
]