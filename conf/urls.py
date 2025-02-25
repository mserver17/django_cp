from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from beauty_salon import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('beauty_salon/', include('beauty_salon.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', RedirectView.as_view(url='beauty_salon/')),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)