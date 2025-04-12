import requests
import PyPDF2
import io
import json
import re
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from pathlib import Path

# Get the directory containing your script
BASE_DIR = Path(__file__).resolve().parent

# Specify the path to your .env file
env_path = BASE_DIR / '.env'

print(f"Looking for .env file at: {env_path}")
load_dotenv(dotenv_path=env_path)

# You can also verify the loaded values immediately after load_dotenv
print(f"Loaded SENDER_EMAIL: {os.getenv('SENDER_EMAIL')}")
print(f"Environment variables loaded from: {env_path}")

def download_pdf(url):
    """Download PDF from URL"""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return io.BytesIO(response.content)
    except requests.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return None

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    try:
        # Create PDF reader object
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def parse_line(line):
    """Parse a single line into a structured event dictionary"""
    try:
        # Match date pattern M/D/YYYY
        date_match = re.match(r'(\d{1,2}/\d{1,2}/\d{4})', line)
        if not date_match:
            return None
        
        date = date_match.group(1)
        print(date)
        remaining_text = line[date_match.end():].strip()
        
        # Match event name (starts with IRONMAN and ends before $ or TBD)
        event_match = re.match(r'(IRONMAN[^$T]+)', remaining_text)
        if not event_match:
            return None
        
        event_name = event_match.group(1).strip()
        print(event_name)
        remaining_text = remaining_text[event_match.end():].strip()
        
        # Match prize purse (either $ amount or TBD)
        prize_match = re.match(r'(\$[\d,]{2,9}|TBD)', remaining_text)
        if not prize_match:
            return None
        
        prize_purse = prize_match.group(1).strip()
        print(prize_purse)
        remaining_text = remaining_text[prize_match.end():].strip()
        
        # Match slot allocation pattern (#WPRO/#MPRO or TBD)
        slot_match = re.match(r'(\d+WPRO/\d+MPRO|TBD)', remaining_text)
        if not slot_match:
            return None
        
        slot_allocation = slot_match.group(1)
        print(slot_allocation)
        remaining_text = remaining_text[slot_match.end():].strip()
        
        # Match registration status (Open, Waitlist, Closed, or TBD)
        status_match = re.search(r'(Open|Waitlist|Closed|CLOSED|TBD)', remaining_text)
        if not status_match:
            return None
        
        registration_status = status_match.group(1)
        # Registration deadline is either the remaining text or TBD
        registration_deadline = remaining_text[status_match.end():].strip()
        if not registration_deadline:
            registration_deadline = "TBD"
        
        return {
            "date": date,
            "event": event_name,
            "prizePurse": prize_purse,
            "slotAllocation": slot_allocation,
            "registrationStatus": registration_status,
            "registrationDeadline": registration_deadline
        }
    except Exception as e:
        print(f"Error parsing line: {line}")
        print(f"Error details: {e}")
        return None
    
def compare_events(new_events, previous_events):
    """Compare new and previous events for changes in registration status or deadline"""
    updates = {}
    
    for event_name, new_event in new_events.items():
        if event_name in previous_events:
            prev_event = previous_events[event_name]
            changes = {}
            
            # Check registration status
            if new_event['registrationStatus'] != prev_event['registrationStatus']:
                changes['registrationStatus'] = {
                    'from': prev_event['registrationStatus'],
                    'to': new_event['registrationStatus']
                }
            
            # Check registration deadline
            if new_event['registrationDeadline'] != prev_event['registrationDeadline']:
                changes['registrationDeadline'] = {
                    'from': prev_event['registrationDeadline'],
                    'to': new_event['registrationDeadline']
                }
            
            if changes:
                updates[event_name] = changes
    
    return updates

def send_update_email(updates):
    """Send email with updates if any exist"""
    if not updates:
        print("No updates to send")
        return
    
    # Email configuration
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('EMAIL_PASSWORD')
    receiver_email = "tombcgordon@gmail.com"

    print('yurt', sender_email, sender_password)
    
    # Validate environment variables
    if not sender_email or not sender_password:
        raise ValueError("Missing email configuration. Please check your .env file.")
    
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

def main():
    # PDF URL
    url = "https://files.constantcontact.com/a202847d001/3eca956c-3919-4cc0-bf2e-018992f61b97.pdf"
    
    # Download PDF
    print("Downloading PDF...")
    pdf_file = download_pdf(url)
    if not pdf_file:
        return
    
    # Extract text
    print("Extracting text...")
    text = extract_text_from_pdf(pdf_file)
    if not text:
        return
    
    # Parse each line and collect events
    events_dict = {}
    for line in text.split('\n'):
        if line.strip() and line.strip()[0].isdigit():
            event_dict = parse_line(line.strip())
            if event_dict:
                # Use event name as the key
                events_dict[event_dict['event']] = event_dict
    
    # Load previous events
    try:
        with open("events_previous.json", "r", encoding="utf-8") as f:
            previous_data = json.load(f)
            previous_events = {event['event']: event for event in previous_data['events']} if 'events' in previous_data else {}
    except FileNotFoundError:
        previous_events = {}
    
    # Compare events and get updates
    updates = compare_events(events_dict, previous_events)
    
    # Print updates if any found
    if updates:
        print("\nUpdates detected:")
        print(json.dumps(updates, indent=2))
        # Send email with updates
        send_update_email(updates)
    else:
        print("\nNo updates detected")
    
    # Convert events_dict to the final output format
    output = {"events": list(events_dict.values())}
    
    # Save to JSON file
    try:
        with open("events_previous.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print("\nData has been saved to events_previous.json")
        
        # Print parsed events for verification
        print("\nParsed Events:")
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(f"Error saving JSON to file: {e}")

if __name__ == "__main__":
    main()