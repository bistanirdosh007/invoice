from django.db import models

# Create your models here.
from django.db import models

class InvoiceFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class InvoiceLog(models.Model):
    client_name = models.CharField(max_length=255)
    email = models.EmailField()
    status = models.CharField(max_length=50)  # e.g., 'Success', 'Failed'
    created_at = models.DateTimeField(auto_now_add=True)
