from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include
from django.conf import settings
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='extrator/')),
    path('admin/', admin.site.urls),
    path('extrator/', include('extrator.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)