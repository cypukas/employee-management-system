from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('employees.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
]
