import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter

def create_invoice_from_template(template_path, output_path, row):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.drawString(200, 750, f"Invoice Number: {row['Invoice Number']}")
    can.drawString(100, 730, f"Customer Name: {row['Customer Name']}")
    can.drawString(100, 710, f"Customer Email: {row['Customer Email']}")
    can.drawString(100, 690, f"Date: {row['Date']}")
    can.drawString(100, 670, f"Total Amount: ${row['Total Amount']}")
    can.save()

    packet.seek(0)
    new_pdf = PdfReader(packet)
    existing_pdf = PdfReader(template_path)
    output = PdfWriter()

    for page in existing_pdf.pages:
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)

    with open(output_path, "wb") as output_stream:
        output.write(output_stream)
