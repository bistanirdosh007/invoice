import os
import pandas as pd
from django.core.files.storage import default_storage
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import render
import yagmail
from decouple import config
import xlwings as xw
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
    file_name = default_storage.save(file.name, file)
    absolute_path = default_storage.path(file_name)
    file.close()
    return absolute_path


def extract_po_number(excel_file):
    """
    Extracts the PO Number from the sheet of the Excel file.
    """
    try:
        first_sheet = excel_file.parse('Sheet1')
        return first_sheet.iloc[1]['PO Number']
    except KeyError:
        raise KeyError("PO Number column is missing in the Excel file.")
    except IndexError:
        raise IndexError("The Excel file is empty or missing required data.")


def convert_sheets_to_pdfs(excel_file_path, po_number, output_dir):
    """
    Converts specified sheets (Statement, SheetB, and SheetC) of the Excel file into PDFs.
    Saves the PDFs in the specified output directory and returns a list of generated PDF file paths.
    """
    target_sheets = ['Statement', 'SheetB', 'SheetC']
    pdf_files = []

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Open the Excel file using xlwings
    with xw.App(visible=False) as app:  # Excel will not be visible during the process
        try:
            wb = app.books.open(excel_file_path)
            print(f"Opened Excel file: {excel_file_path}")
        except Exception as e:
            print(f"Error opening Excel file: {e}")
            return []

        # Iterate through the sheets and convert them to PDF
        for sheet_name in target_sheets:
            if sheet_name in [sheet.name for sheet in wb.sheets]:  # Match sheet names exactly
                sheet = wb.sheets[sheet_name]
                print(f"Processing sheet: {sheet_name}")

                # Generate the PDF file path in the same directory as the uploaded file
                pdf_file_name = f"{sheet_name}_PO_{po_number}.pdf"
                pdf_file_path = os.path.join(output_dir, pdf_file_name)
                print(f"Generated PDF path: {pdf_file_path}")
                pdf_files.append(pdf_file_path)

                # Check if sheet has any content
                if sheet.used_range.count > 0:
                    try:
                        # Convert the sheet to PDF
                        print(f"Converting sheet {sheet_name} to PDF...")
                        sheet.api.ExportAsFixedFormat(0, pdf_file_path)
                        print(f"PDF saved: {pdf_file_path}")
                    except Exception as e:
                        print(f"Error converting sheet {sheet_name} to PDF: {e}")
                        continue
                else:
                    print(f"Sheet {sheet_name} is empty, skipping PDF conversion.")
            else:
                print(f"Warning: {sheet_name} is missing in the Excel file.")

        # Close the workbook
        wb.close()
        print(f"Closed Excel file: {excel_file_path}")

    return pdf_files


def send_email_with_attachments(email_address, pdf_files, po_number):
    """
    Sends an email with the generated PDFs as attachments.
    """
    try:
        # Retrieve email credentials from environment variables using decouple
        email_user = config('EMAIL_USER')

        # Initialize yagmail client
        yag = yagmail.SMTP(user=email_user, password=config('EMAIL_PASSWORD'))

        # Compose and send the email
        subject = f'Excel Sheets Converted to PDFs - PO Number {po_number}'
        body = 'Attached are the PDF files generated from your Excel file.'
        yag.send(to=email_address, subject=subject, contents=body, attachments=pdf_files)

        print(f"Email successfully sent to {email_address}.")

    except Exception as e:
        print(f"Error sending email: {e}")
        raise


def process_excel(request):
    """
    Main function to handle the uploaded Excel file and ask where to save the PDFs.
    """
    if request.method == 'POST' and request.FILES.get('excelFile'):
        uploaded_file = request.FILES['excelFile']
        
        # Get the save directory from the form input, if provided
        save_directory = request.POST.get('saveDirectory')
        
        # If save directory is not provided, use the uploaded file's temporary directory
        if not save_directory:
            save_directory = os.path.dirname(uploaded_file.name)
        
        # Print the selected directory for debugging
        print(f"Save directory: {save_directory}")

        try:
            # Step 1: Save the uploaded file temporarily (get the file path)
            full_file_path = save_uploaded_file(uploaded_file)
            
            # Step 2: Read the Excel file
            excel_file = pd.ExcelFile(full_file_path)

            # Step 3: Extract PO Number
            po_number = extract_po_number(excel_file)

            # Step 4: Convert sheets to PDFs
            pdf_files = convert_sheets_to_pdfs(excel_file, po_number, save_directory)

            # Step 5: Send email if address is provided
            email_address = request.POST.get('email')
            recipient_type = request.POST.get('recipientType')  # Recipient type (e.g., warehouse, customer)
            if email_address:
                send_email_with_attachments(email_address, pdf_files, po_number)

                # Step 6: Log the email in the database
                EmailLog.objects.create(
                    recipient_type=recipient_type,
                    email_address=email_address,
                    pdf_file_paths=",".join(pdf_files),
                )

            # Step 7: Return success response
            return JsonResponse({'message': 'PDFs created and email sent successfully', 'pdf_files': pdf_files})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        finally:
            # Step 8: Clean up the uploaded Excel file
            if os.path.exists(full_file_path):
                try:
                    os.remove(full_file_path)
                except Exception as cleanup_error:
                    print(f"Error cleaning up file: {cleanup_error}")

    return JsonResponse({'error': 'Invalid request'}, status=400)
