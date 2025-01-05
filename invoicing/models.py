from django.db import models

class EmailLog(models.Model):
    recipient_type = models.CharField(max_length=100)
    email_address = models.EmailField()
    pdf_file_paths = models.TextField()  # Store PDF paths as a comma-separated string
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Email to {self.email_address} ({self.recipient_type}) on {self.sent_at}"
