from django.shortcuts import render
from django.contrib import messages
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from chromedriver_py import binary_path
import pandas as pd
import time
import os
import re

def track_deliveries(request):
    updated_rows = []  # To store details of updated rows

    if request.method == "POST" and request.FILES.get("file"):
        # Save uploaded file
        file = request.FILES["file"]
        file_path = os.path.join(file.name)  # Save file in "uploads" directory

        with open(file_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Read the Excel file
        try:
            df = pd.read_excel(file_path)

            # Set up Selenium WebDriver
            svc = Service(executable_path=binary_path)
            driver = webdriver.Chrome(service=svc)

            # Iterate through rows
            for index, row in df.iterrows():
                if row["Status"] != "Delivered":
                    tracking_number = row["Tracking Number"]
                    forwarder = row["Freight Forwarder"].lower()

                    try:
                        # Determine the URL based on forwarder
                        if forwarder == "ups":
                            url = f"https://www.ups.com/track?track=yes&trackNums={tracking_number}&loc=en_US&requester=ST/trackdetails"
                        elif forwarder == "fastfrate":
                            url = f"https://apps.fastfrate.com/fastnet/FastNet.aspx?ProbillNo={tracking_number}"  
                        elif forwarder == "dayross":
                            url = f"https://dayross.com/view-shipment-tracking?division=Freight&probillNumber={tracking_number}"  
                        else:
                            continue

                        # Visit the page and check delivery status
                        driver.get(url)
                        time.sleep(10)  # Wait for the page to load
                        page_text = driver.find_element(By.TAG_NAME, "body").text

                        # Check for 'Delivered' in the page text
                        if re.search(r"\bdelivered\b", page_text, re.IGNORECASE):
                            delivery_status = "Delivered"
                        else:
                            delivery_status = "Not Delivered"

                        # Update DataFrame and log updated rows
                        df.at[index, "Status"] = delivery_status
                        updated_rows.append({
                            "Tracking_Number": tracking_number,
                            "Freight_Forwarder": forwarder,
                            "Status": delivery_status
                        })
                    except Exception as e:
                        df.at[index, "Status"] = f"Error: {str(e)}"

            # Save the updated Excel file
            df.to_excel(file_path, index=False, engine="openpyxl")
            driver.quit()  # Close Selenium WebDriver

            # Display success message
            messages.success(request, "File processed successfully!")

        except Exception as e:
            messages.error(request, f"Error processing the file: {str(e)}")
            return render(request, "track_delivery/upload.html")

        # Render page with updated details
        return render(request, "track_delivery/upload.html", {"updated_rows": updated_rows})

    return render(request, "track_delivery/upload.html")
