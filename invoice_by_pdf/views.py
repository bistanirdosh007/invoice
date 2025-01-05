from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import InvoiceFile
from .utils.invoice_processor import process_invoices
from .forms import InvoiceFileForm
from django.contrib import messages

def upload_invoice(request):
    if request.method == 'POST':
        form = InvoiceFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.save()
            process_invoices(file.file.path)  # Process the file
            messages.success(request, "Invoices processed and mails sent successfully!")
            return redirect('/invoicing-by-pdf/upload/')
    else:
        form = InvoiceFileForm()
    return render(request, 'invoice_by_pdf/upload.html', {'form': form})
