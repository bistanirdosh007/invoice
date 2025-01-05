import os
import pandas as pd
from django.core.files.storage import default_storage
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import render
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from django.conf import settings
from .models import EmailLog


def render_upload_excel(request):
    """
    Renders the HTML upload page for the user.
    """
    return render(request, 'invoicing/upload.html')


def save_uploaded_file(file):
    """
    Saves the uploaded file to a temporary location.
    Returns the full file path of the saved file.
    """
    file_name = file.name
    print(f"Original file name: {file_name}")
    
    # Save the file with a unique name
    file_path = default_storage.save(file_name, file)
    absolute_path = default_storage.path(file_path)  # Get the absolute path from default_storage
    
    print(f"Saved file path: {absolute_path}")

    # Close the file after saving it (if needed)
    file.close()  # Close the file-like object to release it

    return absolute_path


def extract_po_number(excel_file):
    """
    Extracts the PO Number from the first sheet of the Excel file.
    Assumes PO Number is in a specific column.
    """
    first_sheet = excel_file.parse('Sheet1')
    try:
        return first_sheet.iloc[0]['PO Number']  # Adjust the row/column index if needed
    except KeyError:
        raise KeyError("PO Number column is missing in the Excel file.")


def convert_sheets_to_pdfs(excel_file, po_number, output_dir):
    """
    Converts only SheetA, SheetB, and SheetC of the Excel file into PDFs.
    Saves the PDFs in the specified output directory.
    Returns a list of generated PDF file paths.
    """
    target_sheets = ['SheetA', 'SheetB', 'SheetC']
    pdf_files = []

    for sheet_name in target_sheets:
        if sheet_name in excel_file.sheet_names:
            data = excel_file.parse(sheet_name)
            pdf_file_name = f"{sheet_name}_PO_{po_number}.pdf"
            pdf_file_path = os.path.join(output_dir, pdf_file_name)
            pdf_files.append(pdf_file_path)

            # Generate the PDF
            with PdfPages(pdf_file_path) as pdf:
                fig, ax = plt.subplots(figsize=(8.5, 11))
                ax.axis('tight')
                ax.axis('off')
                ax.table(cellText=data.values, colLabels=data.columns, loc='center')
                pdf.savefig(fig)
                plt.close(fig)
        else:
            print(f"Warning: {sheet_name} is missing in the Excel file.")

    return pdf_files

def send_email_with_attachments(email_address, pdf_files, po_number):
    """
    Sends an email with the generated PDFs as attachments.
    """
    email = EmailMessage(
        subject=f'Excel Sheets Converted to PDFs - PO Number {po_number}',
        body='Attached are the PDF files generated from your Excel file.',
        to=[email_address]
    )
    for pdf_file in pdf_files:
        email.attach_file(pdf_file)
    email.send()


def process_excel(request):
    """
    Main function to handle the uploaded Excel file.
    This function orchestrates all the sub-tasks and logs the email sent.
    """
    if request.method == 'POST' and request.FILES.get('excelFile'):
        uploaded_file = request.FILES['excelFile']

        try:
            # Step 1: Save the uploaded file
            full_file_path = save_uploaded_file(uploaded_file)

            # Step 2: Read the Excel file
            excel_file = pd.ExcelFile(full_file_path)

            # Step 3: Extract PO Number
            po_number = extract_po_number(excel_file)

            # Step 4: Convert sheets to PDFs
            output_dir = os.path.dirname(full_file_path)
            pdf_files = convert_sheets_to_pdfs(excel_file, po_number, output_dir)

            # Step 5: (Optional) Send email if address is provided
            email_address = request.POST.get('email')
            recipient_type = request.POST.get('recipientType')  # Recipient type (e.g., warehouse, customer)
            if email_address:
                # Send the email with the generated PDFs
                send_email_with_attachments(email_address, pdf_files, po_number)

                # Step 6: Save email details in the database
                email_log = EmailLog.objects.create(
                    recipient_type=recipient_type,
                    email_address=email_address,
                    pdf_file_paths=",".join(pdf_files),  # Save as a comma-separated string
                )
                email_log.save()

            # Step 7: Return success response
            return JsonResponse({'message': 'PDFs created and email sent successfully', 'pdf_files': pdf_files})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        # finally:
        #     # Step 8: Clean up the uploaded Excel file
        #     if os.path.exists(full_file_path):
        #         os.remove(full_file_path)

    return JsonResponse({'error': 'Invalid request'}, status=400)
