from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('guest.urls')),
    path('', include('account.urls')),
    re_path(r'^i18n/', include('django.conf.urls.i18n')),  # veya path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('account/', include('account.urls')),
    path('guest/', include('guest.urls')),
    # Diğer uygulamalarınızın URL'leri
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    ]
