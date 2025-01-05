import pandas as pd
from PyPDF2 import PdfReader, PdfWriter # type: ignore
from reportlab.pdfgen import canvas # type: ignore 
from reportlab.lib.pagesizes import letter # type: ignore
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from .models import InvoiceLog
import io
import os
import shutil

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd

def process_invoices(file_path):
    data = pd.read_excel(file_path)
    template_pdf_path = "E:/MoltonRox/invoice_system/Invoice Template.pdf"  # Path to your template PDF
    sender_email = "avyamtech@gmail.com"
    password = "obtecbxokpyilprs"

    for _, row in data.iterrows():
        try:
            # Create a new PDF based on the template
            output_pdf_path = f"invoice_{row['Invoice Number']}.pdf"
            create_invoice_from_template(template_pdf_path, output_pdf_path, row)

            # Send Email
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = row['Customer Email']
            msg['Subject'] = f"Invoice {row['Invoice Number']}"
            
            # Check if the file exists before attaching
            if not os.path.exists(output_pdf_path):
                raise FileNotFoundError(f"PDF file {output_pdf_path} does not exist.")

            with open(output_pdf_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename={output_pdf_path}")
                msg.attach(part)

            # Establish SMTP connection
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
            server.quit()

            # Log Success
            InvoiceLog.objects.create(
                client_name=row['Customer Name'],
                email=row['Customer Email'],
                status='Success'
            )
            # Delete the temporary file after sending the email
            os.remove(output_pdf_path)
            if os.path.exists("uploads/"):
                shutil.rmtree('uploads/')

        except Exception as e:
            # Log Failure
            print(f"Error sending email for invoice {row['Invoice Number']}: {e}")
            InvoiceLog.objects.create(
                client_name=row['Customer Name'],
                email=row['Customer Email'],
                status=f"Failed: {e}"
            )

def create_invoice_from_template(template_path, output_path, row):
    """
    Populate the template PDF with invoice data.
    """
    # Create a buffer for the new PDF content
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Populate data on the template
    can.drawString(200, 750, f"Invoice Number: {row['Invoice Number']}")
    can.drawString(100, 730, f"Customer Name: {row['Customer Name']}")
    can.drawString(100, 710, f"Customer Email: {row['Customer Email']}")
    can.drawString(100, 690, f"Date: {row['Date']}")
    can.drawString(100, 670, f"Total Amount: ${row['Total Amount']}")
    can.save()

    # Merge the overlay with the template
    packet.seek(0)
    new_pdf = PdfReader(packet)
    existing_pdf = PdfReader(template_path)
    output = PdfWriter()

    for page in existing_pdf.pages:
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)

    # Save the final PDF
    with open(output_path, "wb") as output_stream:
        output.write(output_stream)
