# invoice_system/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('invoicing_by_pdf/', include('invoice_by_pdf.urls')),
    path('track_delivery/', include('track_delivery.urls')),
    path('send_emails/', include('invoicing.urls')),

]
