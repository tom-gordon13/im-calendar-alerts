import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os

def send_update_email(updates):
    """Send email with updates if any exist"""
    if not updates:
        print("No updates to send")
        return
    
    # Email configuration
    sender_email = os.getenv('SENDER_EMAIL') 
    sender_password = os.getenv('EMAIL_PASSWORD')
    receiver_email = "tombcgordon@gmail.com"
    
    # Create message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "IRONMAN Event Updates Detected"
    
    # Create the email body
    body = "The following updates have been detected:\n\n"
    
    for event_name, changes in updates.items():
        body += f"Event: {event_name}\n"
        if 'registrationStatus' in changes:
            body += f"Registration Status changed from '{changes['registrationStatus']['from']}' to '{changes['registrationStatus']['to']}'\n"
        if 'registrationDeadline' in changes:
            body += f"Registration Deadline changed from '{changes['registrationDeadline']['from']}' to '{changes['registrationDeadline']['to']}'\n"
        body += "\n"
    
    # Add body to email
    message.attach(MIMEText(body, "plain"))
    
    try:
        # Create SMTP session
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            if not sender_password:
                raise ValueError("Email password not found in environment variables")
            
            server.login(sender_email, sender_password)
            text = message.as_string()
            server.sendmail(sender_email, receiver_email, text)
            print("Update email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")
