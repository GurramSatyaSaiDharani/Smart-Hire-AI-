import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@smarthire.ai")

def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    """
    Sends an email notification if SMTP credentials are configured.
    Otherwise, logs the email preview to console without crashing.
    """
    print(f"--- EMAIL NOTIFICATION [To: {to_email}] ---")
    print(f"Subject: {subject}")
    print(f"Body: {body[:150]}...")
    print("--------------------------------------------")

    if not EMAIL_HOST or not EMAIL_USERNAME or not EMAIL_PASSWORD:
        print("Notice: SMTP configuration not set. Email logged in development mode.")
        return True

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, to_email, msg.as_string())
        server.quit()
        print(f"Successfully delivered email to {to_email}")
        return True
    except Exception as e:
        print(f"Warning: Email delivery failed to {to_email}: {e}")
        return False
