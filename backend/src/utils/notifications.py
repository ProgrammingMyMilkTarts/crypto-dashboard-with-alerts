# backend/src/utils/notifications.py
import os
import logging
from twilio.rest import Client
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

load_dotenv(override=True)
logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')

def send_whatsapp(to_number:str,message_body:str):
    #this is to send the whatsapp message using TwilioAPI
    print("This is the send whatsapp")

def send_email(to_email: str, subject:str,html_content: str):
    #send email
    try:
        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')

        # Build MIME message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to_email

        # Attach HTML body
        part = MIMEText(html_content, "html")
        msg.attach(part)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user,smtp_password)
            server.sendmail(smtp_user,to_email,msg.as_string())
        logging.info(f"Email send to {to_email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        return False

def send_notification(method:str,contact:str,symbol:str,current_price:float,condition:str,target_price:float,unsub_token:str):
    """Router function called by price_checker to dispatch via the user's chosen method."""
    
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    unsub_link = f"{frontend_url}/unsubscribe?token={unsub_token}"

    if method.lower() == 'email':
        subject = f"Alert: {symbol} hit ${current_price:,.2f}!"
        html_content = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                <h2 style="color: #e67e22;">Crypto Price Alert Triggered</h2>
                <p>Your target for <strong>{symbol}</strong> has been reached.</p>
                <ul>
                    <li><strong>Current Price:</strong> ${current_price:,.2f}</li>
                    <li><strong>Condition:</strong> Price went {condition} target ${target_price:,.2f}</li>
                </ul>
                <br>
                <p style="font-size: 12px; color: #777;">
                    Don't want these alerts anymore? <a href="{unsub_link}">Unsubscribe instantly</a>.
                </p>
            </div>
        """
        return send_email(contact, subject, html_content)

    else:
        logging.warning(f"Unknown notification method specified: {method}")
        return False