from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('beauty_salon/', include('beauty_salon.urls')),
    path('', RedirectView.as_view(url='beauty_salon/')),
    # path('accounts/', include('django.contrib.auth.urls')),
]