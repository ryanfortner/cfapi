import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gspread
from google.oauth2.service_account import Credentials
from Constants import *

def get_subscribers():
    """Reads the Google Sheet and returns a list of unique email addresses."""
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        
        # 1. Grab the raw JSON string from the environment variable
        creds_json_str = os.getenv("GCP_CREDENTIALS")
        
        if not creds_json_str:
            print("[!] GCP_CREDENTIALS environment variable not found. Cannot fetch subscribers.")
            return []
            
        # 2. Parse the string into a Python dictionary
        creds_dict = json.loads(creds_json_str)
        
        # 3. Load the credentials from the dictionary instead of a file path
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Open the sheet and grab the first tab
        sheet = client.open_by_url(SHEETS_URL).sheet1
        
        # Assuming Form timestamps are in Col 1 (A), and Emails are in Col 2 (B)
        emails = sheet.col_values(2)[1:] 
        
        # Clean up empty strings and remove duplicates using set()
        cleaned_emails = list(set([e.strip() for e in emails if e.strip()]))
        return cleaned_emails
        
    except Exception as e:
        print(f"[!] Error fetching subscribers from Google Sheets: {e}")
        return []

def send_alerts(offer_name, expires_text):
    """Emails all subscribers about the new offer."""
    
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("[!] Gmail credentials missing from environment. Cannot send emails.")
        return

    emails = get_subscribers()
    if not emails:
        print("[*] No subscribers found to notify.")
        return

    print(f"[*] Sending email alerts to {len(emails)} subscribers...")

    try:
        # Connect to Gmail's outgoing SMTP server securely
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    except Exception as e:
        print(f"[!] Failed to connect to Gmail SMTP: {e}")
        return

    for email in emails:
        msg = MIMEMultipart()
        msg['From'] = f"Raleigh CFA Alerts <{GMAIL_USER}>"
        msg['To'] = email
        msg['Subject'] = f"🚨 FREE Chick-fil-A Alert: {offer_name}!"

        body = f"""Hey there!\n\nA new local reward has dropped in the area: {offer_name}\n\nOpen your Chick-fil-A app to claim it.\nIt expires on: {expires_text}\n\nEnjoy!"""
        msg.attach(MIMEText(body, 'plain'))

        try:
            server.send_message(msg)
        except Exception as e:
            print(f"[!] Failed to send to {email}: {e}")

    server.quit()
    print("[*] All email alerts dispatched successfully.")