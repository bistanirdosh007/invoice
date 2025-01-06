# invoice_system/urls.py
from django.contrib import admin
from django.urls import path, include
from . import views  

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('track_delivery/', include('track_delivery.urls')),
    path('send_emails/', include('invoicing.urls')),

]
