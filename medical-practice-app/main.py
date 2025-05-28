#!/usr/bin/env python3
"""
Medical Practice Management Desktop Application
A modern PyWebView-based desktop application for Windows
"""

import os
import sys
import json
import threading
import logging
import datetime
import webview
from pathlib import Path
import queue
import base64
import csv
import tempfile

# Import existing backend modules
from backend.azure_services import AzureServices, SecureConfig
from backend.auth_manager import AdminCredentials
from backend.data_models import DoctorManager, LabManager, PharmacyManager

# Set up logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"app_{datetime.datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MedicalPracticeAPI:
    """API class for PyWebView that handles all backend operations"""
    
    def __init__(self):
        self.config = SecureConfig()
        self.credentials = AdminCredentials()
        self.azure = None
        self.authenticated = False
        self.current_user = None
        self.theme = 'light'
        self.window = None
        
        # Data caches
        self.doctors_data = []
        self.labs_data = []
        self.pharmacies_data = []
        
        # Initialize managers
        self.doctor_manager = None
        self.lab_manager = None
        self.pharmacy_manager = None
        
        # Session management
        self.session_start = None
        self.last_activity = None
        
    def set_window(self, window):
        """Set the webview window reference"""
        self.window = window
        
    def initialize(self):
        """Initialize the application"""
        try:
            # Initialize Azure services
            self.azure = AzureServices(self.config)
            
            # Initialize managers
            self.doctor_manager = DoctorManager(self.azure)
            self.lab_manager = LabManager(self.azure)
            self.pharmacy_manager = PharmacyManager(self.azure)
            
            return {'success': True, 'message': 'Application initialized'}
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Authentication Methods
    def login(self, username, password):
        """Authenticate user"""
        try:
            success, message = self.credentials.authenticate(username, password)
            
            if success:
                self.authenticated = True
                self.current_user = username
                self.session_start = datetime.datetime.now(datetime.timezone.utc)
                self.last_activity = datetime.datetime.now(datetime.timezone.utc)
                
                # Check if password change required
                require_change = self.credentials.credentials.get('require_password_change', False)
                
                return {
                    'success': True,
                    'username': username,
                    'requirePasswordChange': require_change,
                    'lastLogin': self.credentials.credentials.get('last_login', 'Never')
                }
            else:
                return {'success': False, 'error': message}
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def logout(self):
        """Logout current user"""
        self.authenticated = False
        self.current_user = None
        self.session_start = None
        self.last_activity = None
        self.doctors_data = []
        self.labs_data = []
        self.pharmacies_data = []
        return {'success': True}
    
    def change_password(self, old_password, new_password):
        """Change admin password"""
        try:
            success = self.credentials.change_password(old_password, new_password)
            if success:
                return {'success': True, 'message': 'Password changed successfully'}
            else:
                return {'success': False, 'error': 'Current password is incorrect'}
        except ValueError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Password change error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def check_session(self):
        """Check if session is still valid"""
        if not self.authenticated:
            return {'valid': False}
        
        valid = self.credentials.is_session_valid()
        if valid:
            self.last_activity = datetime.datetime.now(datetime.timezone.utc)
        
        return {
            'valid': valid,
            'remainingMinutes': self._get_remaining_session_time()
        }
    
    def _get_remaining_session_time(self):
        """Get remaining session time in minutes"""
        if not self.session_start:
            return 0
        
        now = datetime.datetime.now(datetime.timezone.utc)
        elapsed = now - self.session_start
        remaining = 30 - (elapsed.total_seconds() / 60)
        return max(0, int(remaining))
    
    # Theme Management
    def get_theme(self):
        """Get current theme"""
        return {'theme': self.theme}
    
    def set_theme(self, theme):
        """Set application theme"""
        self.theme = theme
        return {'success': True, 'theme': theme}
    
    # Data Operations
    def get_doctors(self):
        """Get all doctors"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            self.doctors_data = self.azure.get_doctor_accounts()
            
            # Process data for frontend
            doctors = []
            for doctor in self.doctors_data:
                subscription_info = self._calculate_subscription_info(doctor)
                doctors.append({
                    'id': doctor.get('id', ''),
                    'name': doctor.get('displayName', ''),
                    'email': doctor.get('email', ''),
                    'status': 'active' if doctor.get('isActive') else 'inactive',
                    'specialty': doctor.get('speciality', ''),
                    'phone': doctor.get('phoneNumber', ''),
                    'pharmacyStatus': 'active' if doctor.get('pharmacyAccountActive') else 'inactive',
                    'labStatus': 'active' if doctor.get('labAccountActive') else 'not_assigned',
                    'subscriptionStart': doctor.get('subscriptionStartDate', ''),
                    'subscriptionEnd': doctor.get('subscriptionEndDate', ''),
                    'daysLeft': subscription_info['daysLeft'],
                    'subscriptionStatus': subscription_info['status']
                })
            
            return {'success': True, 'data': doctors}
        except Exception as e:
            logger.error(f"Failed to get doctors: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_labs(self):
        """Get all laboratories"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            self.labs_data = self.azure.get_lab_accounts()
            
            # Process data for frontend
            labs = []
            for lab in self.labs_data:
                # Find associated doctor
                doctor = next((d for d in self.doctors_data if d['id'] == lab.get('doctorId')), None)
                doctor_name = doctor.get('displayName', 'Unknown') if doctor else 'Unknown'
                
                labs.append({
                    'id': lab.get('id', ''),
                    'name': lab.get('name', ''),
                    'doctorId': lab.get('doctorId', ''),
                    'doctorName': doctor_name,
                    'status': 'active' if lab.get('isActive') else 'inactive',
                    'accessCode': lab.get('accessCode', ''),
                    'createdAt': lab.get('createdAt', '')
                })
            
            return {'success': True, 'data': labs}
        except Exception as e:
            logger.error(f"Failed to get labs: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_pharmacies(self):
        """Get all pharmacies"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            self.pharmacies_data = self.azure.get_pharmacy_accounts()
            
            # Process data for frontend
            pharmacies = []
            for pharmacy in self.pharmacies_data:
                # Find associated doctor
                doctor = next((d for d in self.doctors_data if d['id'] == pharmacy.get('doctorId')), None)
                doctor_name = doctor.get('displayName', 'Unknown') if doctor else 'Unknown'
                
                pharmacies.append({
                    'id': pharmacy.get('id', ''),
                    'name': pharmacy.get('name', ''),
                    'doctorId': pharmacy.get('doctorId', ''),
                    'doctorName': doctor_name,
                    'status': 'active' if pharmacy.get('isActive') else 'inactive',
                    'accessCode': pharmacy.get('accessCode', ''),
                    'createdAt': pharmacy.get('createdAt', '')
                })
            
            return {'success': True, 'data': pharmacies}
        except Exception as e:
            logger.error(f"Failed to get pharmacies: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_subscriptions(self):
        """Get subscription data"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            subscriptions = []
            for doctor in self.doctors_data:
                subscription_info = self._calculate_subscription_info(doctor)
                subscriptions.append({
                    'id': doctor.get('id', ''),
                    'name': doctor.get('displayName', ''),
                    'email': doctor.get('email', ''),
                    'startDate': doctor.get('subscriptionStartDate', ''),
                    'endDate': doctor.get('subscriptionEndDate', ''),
                    'daysLeft': subscription_info['daysLeft'],
                    'status': subscription_info['status']
                })
            
            return {'success': True, 'data': subscriptions}
        except Exception as e:
            logger.error(f"Failed to get subscriptions: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            # Calculate statistics
            total_doctors = len(self.doctors_data)
            active_subs = sum(1 for d in self.doctors_data 
                            if self._calculate_subscription_info(d)['status'] == 'active')
            expiring_soon = sum(1 for d in self.doctors_data 
                              if self._calculate_subscription_info(d)['status'] == 'warning')
            expired = sum(1 for d in self.doctors_data 
                        if self._calculate_subscription_info(d)['status'] == 'expired')
            
            return {
                'success': True,
                'stats': {
                    'totalDoctors': total_doctors,
                    'activeSubscriptions': active_subs,
                    'expiringSoon': expiring_soon,
                    'expired': expired
                }
            }
        except Exception as e:
            logger.error(f"Failed to get dashboard stats: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_doctor(self, doctor_data):
        """Create new doctor account"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            result = self.azure.create_doctor_account(doctor_data)
            
            return {
                'success': True,
                'data': {
                    'doctorId': result['doctor_id'],
                    'email': result['doctor_email'],
                    'password': result['doctor_password'],
                    'pharmacyCode': result['pharmacy_code'],
                    'labCode': result['lab_code']
                }
            }
        except Exception as e:
            logger.error(f"Failed to create doctor: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def update_doctor(self, doctor_id, update_data):
        """Update doctor information"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            result = self.azure.update_doctor_account(doctor_id, update_data)
            return {'success': True, 'data': result}
        except Exception as e:
            logger.error(f"Failed to update doctor: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def reset_doctor_password(self, doctor_id):
        """Reset doctor password"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            new_password = self.azure.reset_doctor_password(doctor_id)
            if new_password:
                return {'success': True, 'password': new_password}
            else:
                return {'success': False, 'error': 'Failed to reset password'}
        except Exception as e:
            logger.error(f"Failed to reset password: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def export_data(self, data_type, ids=None):
        """Export data to CSV"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
            
            with open(temp_file.name, 'w', newline='', encoding='utf-8') as file:
                if data_type == 'doctors':
                    headers = ["ID", "Name", "Email", "Status", "Specialty", "Phone", 
                             "Subscription Start", "Subscription End", "Days Left"]
                    writer = csv.writer(file)
                    writer.writerow(headers)
                    
                    for doctor in self.doctors_data:
                        if ids and doctor['id'] not in ids:
                            continue
                        
                        subscription_info = self._calculate_subscription_info(doctor)
                        writer.writerow([
                            doctor.get('id', ''),
                            doctor.get('displayName', ''),
                            doctor.get('email', ''),
                            'Active' if doctor.get('isActive') else 'Inactive',
                            doctor.get('speciality', ''),
                            doctor.get('phoneNumber', ''),
                            doctor.get('subscriptionStartDate', '')[:10],
                            doctor.get('subscriptionEndDate', '')[:10],
                            subscription_info['daysLeft'] if subscription_info['daysLeft'] is not None else 'N/A'
                        ])
            
            # Read file and encode as base64
            with open(temp_file.name, 'rb') as file:
                file_data = base64.b64encode(file.read()).decode('utf-8')
            
            # Clean up
            os.unlink(temp_file.name)
            
            return {
                'success': True,
                'data': file_data,
                'filename': f"{data_type}_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        except Exception as e:
            logger.error(f"Failed to export data: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_subscription_info(self, doctor):
        """Calculate subscription information"""
        end_date_str = doctor.get('subscriptionEndDate', '')
        
        if not end_date_str:
            return {'daysLeft': None, 'status': 'unknown'}
        
        try:
            # Parse the datetime string
            if 'T' in end_date_str:
                end_dt = datetime.datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            else:
                end_dt = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
            
            # Ensure timezone awareness
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=datetime.timezone.utc)
            
            # Calculate days left
            now = datetime.datetime.now(datetime.timezone.utc)
            days_left = (end_dt - now).days
            
            # Determine status
            if days_left < 0:
                status = 'expired'
            elif days_left <= 30:
                status = 'warning'
            else:
                status = 'active'
            
            return {'daysLeft': days_left, 'status': status}
        except Exception as e:
            logger.error(f"Error calculating subscription: {e}")
            return {'daysLeft': None, 'status': 'unknown'}
    
    def show_file_dialog(self, dialog_type='save', file_types='CSV files (*.csv)|*.csv'):
        """Show file dialog"""
        if self.window:
            if dialog_type == 'save':
                result = self.window.create_file_dialog(
                    webview.SAVE_DIALOG,
                    save_filename=f'export_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                    file_types=(file_types,)
                )
            else:
                result = self.window.create_file_dialog(
                    webview.OPEN_DIALOG,
                    file_types=(file_types,)
                )
            
            return {'success': True, 'path': result[0] if result else None}
        return {'success': False, 'error': 'Window not initialized'}

def get_html_content():
    """Get the main HTML content"""
    html_path = Path(__file__).parent / 'templates' / 'index.html'
    if html_path.exists():
        return html_path.read_text(encoding='utf-8')
    else:
        # Return embedded HTML if file not found
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medical Practice Management</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: #f5f5f5;
        }
        .loading {
            text-align: center;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="loading">
        <div class="spinner"></div>
        <h2>Loading Medical Practice Management...</h2>
        <p>Please wait while we initialize the application.</p>
    </div>
</body>
</html>"""

def main():
    """Main entry point"""
    # Create API instance
    api = MedicalPracticeAPI()
    
    # Initialize backend
    init_result = api.initialize()
    if not init_result['success']:
        logger.error(f"Failed to initialize: {init_result.get('error')}")
        sys.exit(1)
    
    # Get HTML content
    html_content = get_html_content()
    
    # Create window
    window = webview.create_window(
        title='Medical Practice Management - Enhanced',
        html=html_content,
        js_api=api,
        width=1400,
        height=900,
        min_size=(1200, 800),
        confirm_close=True,
        text_select=True
    )
    
    # Set window reference
    api.set_window(window)
    
    # Start the application
    webview.start(debug=True, gui='edgechromium')

if __name__ == '__main__':
    main()