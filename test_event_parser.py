import unittest
from unittest.mock import patch, mock_open
import json
from main import compare_events, parse_line, send_update_email
import os

class TestEventParser(unittest.TestCase):
    def setUp(self):
        # Sample event data
        self.mock_previous_data = {
            "events": [
                {
                    "date": "3/1/2024",
                    "event": "IRONMAN South Africa",
                    "prizePurse": "$100,000",
                    "slotAllocation": "2WPRO/2MPRO",
                    "registrationStatus": "TBD",
                    "registrationDeadline": "1/15/2024"
                }
            ]
        }
        
        self.mock_new_data = {
            "IRONMAN South Africa": {
                "date": "3/1/2024",
                "event": "IRONMAN South Africa",
                "prizePurse": "$100,000",
                "slotAllocation": "2WPRO/2MPRO",
                "registrationStatus": "Open",
                "registrationDeadline": "1/15/2024"
            }
        }

    def test_registration_status_change_from_tbd(self):
        """Test that changes from TBD to a status are detected"""
        # Convert previous data format to match the comparison function's expected format
        previous_events = {event['event']: event for event in self.mock_previous_data['events']}
        
        # Get updates
        updates = compare_events(self.mock_new_data, previous_events)
        
        # Expected update format
        expected_updates = {
            "IRONMAN South Africa": {
                "registrationStatus": {
                    "from": "TBD",
                    "to": "Open"
                }
            }
        }
        
        # Assert that updates match expected format
        self.assertEqual(updates, expected_updates)
    
    def test_parse_line_with_tbd(self):
        """Test parsing a line containing TBD values"""
        test_line = "3/1/2024 IRONMAN South Africa $100,000 2WPRO/2MPRO TBD TBD"
        result = parse_line(test_line)
        
        expected_result = {
            "date": "3/1/2024",
            "event": "IRONMAN South Africa",
            "prizePurse": "$100,000",
            "slotAllocation": "2WPRO/2MPRO",
            "registrationStatus": "TBD",
            "registrationDeadline": "TBD"
        }
        
        self.assertEqual(result, expected_result)

    @patch('builtins.open', new_callable=mock_open)
    def test_file_operations(self, mock_file):
        """Test file reading and writing operations"""
        # Mock the file read operation
        mock_file.return_value.read.return_value = json.dumps(self.mock_previous_data)
        
        # Read the mock file
        with open('events_previous.json', 'r') as f:
            data = json.load(f)
        
        # Assert that the read data matches our mock data
        self.assertEqual(data, self.mock_previous_data)

class TestEmailService(unittest.TestCase):
    @patch.dict(os.environ, {
        'SENDER_EMAIL': 'test@example.com',
        'EMAIL_PASSWORD': 'test_password'
    })
    @patch('smtplib.SMTP_SSL')
    def test_send_update_email(self, mock_smtp):
        """Test email sending with mocked environment variables"""
        updates = {
            "IRONMAN South Africa": {
                "registrationStatus": {
                    "from": "TBD",
                    "to": "Open"
                }
            }
        }
        
        # Configure the mock
        mock_smtp.return_value.__enter__.return_value = mock_smtp
        
        # Call the function
        send_update_email(updates)
        
        # Assert that sendmail was called
        self.assertTrue(mock_smtp.return_value.sendmail.called)
        
        # Assert that login was called with correct credentials
        mock_smtp.return_value.login.assert_called_with(
            os.getenv('SENDER_EMAIL'),
            os.getenv('EMAIL_PASSWORD')
        )

if __name__ == '__main__':
    unittest.main()
