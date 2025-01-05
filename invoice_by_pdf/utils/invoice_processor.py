import pandas as pd
import os
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from .pdf_generator import create_invoice_from_template
from .email_helper import send_email
from ..models import InvoiceLog
from string import Template

def process_invoices(file_path):
    data = pd.read_excel(file_path)
    template_pdf_path = "E:/MoltonRox/invoice_system/Invoice Template.pdf"  # Template path
    sender_email = "avyamtech@gmail.com"
    password = "obtecbxokpyilprs"

    for _, row in data.iterrows():
        try:
            # Generate PDF
            output_pdf_path = f"invoice_{row['Invoice Number']}.pdf"
            create_invoice_from_template(template_pdf_path, output_pdf_path, row)

            # Load the HTML template
            with open('invoice_template.html', 'r') as file:
                template = Template(file.read())

            # Send Email
            email_body = f"""
            Dear {row['Customer Name']},
            Thank you for your business. Please find your invoice attached.
            Invoice Number: {row['Invoice Number']}
            Total Amount: ${row['Total Amount']}
            """
            send_email(
                sender_email=sender_email,
                password=password,
                recipient=row['Customer Email'],
                subject=f"Invoice {row['Invoice Number']}",
                body=email_body,
                attachment_path=output_pdf_path
            )

            # Log success
            InvoiceLog.objects.create(
                client_name=row['Customer Name'],
                email=row['Customer Email'],
                status='Success'
            )

            # Cleanup temporary file
            os.remove(output_pdf_path)

        except Exception as e:
            # Log failure
            InvoiceLog.objects.create(
                client_name=row['Customer Name'],
                email=row['Customer Email'],
                status=f"Failed: {e}"
            )
