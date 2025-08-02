#!/usr/bin/env python3
"""
Employee Onboarding Assistant - API Integration Demo
Demonstrates workflow automation with multiple API integrations
Perfect for IFS Junior AI Engineer application
"""

import requests
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import logging
from typing import Dict, List
import os
from dataclasses import dataclass

@dataclass
class Employee:
    name: str
    email: str
    department: str
    start_date: str
    manager: str

class OnboardingAssistant:
    def __init__(self):
        """Initialize the onboarding assistant with API configurations"""
        self.setup_logging()
        self.config = self.load_config()
        
    def setup_logging(self):
        """Configure logging for monitoring workflow execution"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('onboarding.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self) -> Dict:
        """Load configuration from environment variables or config file"""
        return {
            'gmail_user': os.getenv('GMAIL_USER', 'your_email@gmail.com'),
            'gmail_password': os.getenv('GMAIL_APP_PASSWORD', 'your_app_password'),
            'slack_webhook': os.getenv('SLACK_WEBHOOK', 'https://hooks.slack.com/your_webhook'),
            'google_sheets_id': os.getenv('SHEETS_ID', 'your_sheet_id'),
            'sheets_api_key': os.getenv('SHEETS_API_KEY', 'your_api_key')
        }
    
    def fetch_new_employees(self) -> List[Employee]:
        """Fetch new employee data from Google Sheets API"""
        try:
            # Google Sheets API endpoint
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{self.config['google_sheets_id']}/values/Sheet1!A:E"
            params = {'key': self.config['sheets_api_key']}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            employees = []
            
            # Skip header row, process employee data
            for row in data.get('values', [])[1:]:
                if len(row) >= 5 and self.is_new_employee(row[3]):  # Check start date
                    employee = Employee(
                        name=row[0],
                        email=row[1],
                        department=row[2],
                        start_date=row[3],
                        manager=row[4]
                    )
                    employees.append(employee)
            
            self.logger.info(f"Found {len(employees)} new employees")
            return employees
            
        except Exception as e:
            self.logger.error(f"Error fetching employees: {str(e)}")
            return []
    
    def is_new_employee(self, start_date: str) -> bool:
        """Check if employee starts within next 7 days"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            today = datetime.now()
            return 0 <= (start - today).days <= 7
        except ValueError:
            return False
    
    def send_welcome_email(self, employee: Employee) -> bool:
        """Send personalized welcome email using Gmail SMTP"""
        try:
            # Create email content
            subject = f"Welcome to the team, {employee.name}!"
            body = self.generate_welcome_email_body(employee)
            
            # Setup email
            msg = MIMEMultipart()
            msg['From'] = self.config['gmail_user']
            msg['To'] = employee.email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.config['gmail_user'], self.config['gmail_password'])
                server.send_message(msg)
            
            self.logger.info(f"Welcome email sent to {employee.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email to {employee.name}: {str(e)}")
            return False
    
    def generate_welcome_email_body(self, employee: Employee) -> str:
        """Generate personalized welcome email content"""
        return f"""
        <html>
        <body>
            <h2>Welcome to Our Team, {employee.name}!</h2>
            
            <p>We're excited to have you join the <strong>{employee.department}</strong> department.</p>
            
            <h3>Your Details:</h3>
            <ul>
                <li><strong>Start Date:</strong> {employee.start_date}</li>
                <li><strong>Department:</strong> {employee.department}</li>
                <li><strong>Manager:</strong> {employee.manager}</li>
            </ul>
            
            <h3>Next Steps:</h3>
            <ol>
                <li>Your manager will contact you within 24 hours</li>
                <li>HR will send you onboarding documents</li>
                <li>IT will setup your accounts and equipment</li>
            </ol>
            
            <p>If you have any questions, please don't hesitate to reach out!</p>
            
            <p>Best regards,<br>
            HR Team</p>
        </body>
        </html>
        """
    
    def notify_slack_team(self, employee: Employee) -> bool:
        """Send team notification to Slack channel"""
        try:
            message = {
                "text": f"🎉 New Team Member Alert!",
                "attachments": [
                    {
                        "color": "good",
                        "fields": [
                            {"title": "Name", "value": employee.name, "short": True},
                            {"title": "Department", "value": employee.department, "short": True},
                            {"title": "Start Date", "value": employee.start_date, "short": True},
                            {"title": "Manager", "value": employee.manager, "short": True}
                        ]
                    }
                ]
            }
            
            response = requests.post(
                self.config['slack_webhook'],
                json=message,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            self.logger.info(f"Slack notification sent for {employee.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending Slack notification: {str(e)}")
            return False
    
    def create_onboarding_checklist(self, employee: Employee) -> Dict:
        """Create onboarding checklist and tasks"""
        checklist = {
            "employee": employee.name,
            "created": datetime.now().isoformat(),
            "tasks": [
                {"task": "Send welcome email", "status": "completed", "owner": "HR"},
                {"task": "Prepare workspace", "status": "pending", "owner": "Facilities"},
                {"task": "Setup IT accounts", "status": "pending", "owner": "IT"},
                {"task": "Schedule first day meeting", "status": "pending", "owner": employee.manager},
                {"task": "Assign buddy/mentor", "status": "pending", "owner": "HR"},
                {"task": "Order business cards", "status": "pending", "owner": "Marketing"}
            ]
        }
        
        # Save checklist to file
        filename = f"checklist_{employee.name.replace(' ', '_').lower()}.json"
        with open(filename, 'w') as f:
            json.dump(checklist, f, indent=2)
        
        self.logger.info(f"Onboarding checklist created for {employee.name}")
        return checklist
    
    def log_workflow_metrics(self, employees_processed: int, success_count: int):
        """Log workflow performance metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "employees_processed": employees_processed,
            "success_count": success_count,
            "success_rate": success_count / employees_processed if employees_processed > 0 else 0,
            "workflow_duration": "automated"
        }
        
        with open('workflow_metrics.json', 'a') as f:
            f.write(json.dumps(metrics) + '\n')
        
        self.logger.info(f"Workflow completed: {success_count}/{employees_processed} successful")
    
    def run_onboarding_workflow(self):
        """Main workflow execution"""
        self.logger.info("Starting onboarding workflow...")
        
        # Step 1: Fetch new employees
        new_employees = self.fetch_new_employees()
        
        if not new_employees:
            self.logger.info("No new employees found")
            return
        
        success_count = 0
        
        # Step 2: Process each employee
        for employee in new_employees:
            self.logger.info(f"Processing onboarding for {employee.name}")
            
            try:
                # Send welcome email
                email_sent = self.send_welcome_email(employee)
                
                # Notify team on Slack
                slack_sent = self.notify_slack_team(employee)
                
                # Create onboarding checklist
                checklist = self.create_onboarding_checklist(employee)
                
                if email_sent and slack_sent:
                    success_count += 1
                    self.logger.info(f"Successfully processed {employee.name}")
                
            except Exception as e:
                self.logger.error(f"Error processing {employee.name}: {str(e)}")
        
        # Step 3: Log metrics
        self.log_workflow_metrics(len(new_employees), success_count)

def main():
    """Main entry point for the onboarding assistant"""
    assistant = OnboardingAssistant()
    assistant.run_onboarding_workflow()

if __name__ == "__main__":
    # Example usage with mock data for demonstration
    print("Employee Onboarding Assistant - API Integration Demo")
    print("=" * 50)
    
    # Create mock employee for testing
    mock_employee = Employee(
        name="John Doe",
        email="john.doe@company.com",
        department="Engineering",
        start_date="2025-08-05",
        manager="Jane Smith"
    )
    
    assistant = OnboardingAssistant()
    
    # Demonstrate individual functions
    print("📧 Generating welcome email...")
    email_body = assistant.generate_welcome_email_body(mock_employee)
    print("✅ Email template generated")
    
    print("\n📋 Creating onboarding checklist...")
    checklist = assistant.create_onboarding_checklist(mock_employee)
    print("✅ Checklist created")
    
    print("\n📊 Logging workflow metrics...")
    assistant.log_workflow_metrics(1, 1)
    print("✅ Metrics logged")
    
    print("\n🎉 Demo completed! Check generated files:")
    print("   - onboarding.log (workflow logs)")
    print("   - checklist_john_doe.json (employee checklist)")
    print("   - workflow_metrics.json (performance metrics)")
    
    print("\n💡 To run with real APIs:")
    print("   1. Set environment variables for API keys")
    print("   2. Update Google Sheets with employee data")
    print("   3. Run: python onboarding_assistant.py")