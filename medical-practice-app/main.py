#!/usr/bin/env python3
"""
Updated Medical Practice Management Desktop Application
Now with minimal login interface - no blue background
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

class BackendService:
    """
    Isolated backend service that handles all Azure operations
    This class is NOT exposed to PyWebView
    """
    
    def __init__(self):
        self.config = None
        self.credentials = None
        self.azure = None
        self.doctor_manager = None
        self.lab_manager = None
        self.pharmacy_manager = None
        self.authenticated = False
        self.current_user = None
        self.session_start = None
        self.last_activity = None
        
        # Data caches
        self.doctors_data = []
        self.labs_data = []
        self.pharmacies_data = []
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize components safely"""
        try:
            self.config = SecureConfig()
            self.credentials = AdminCredentials()
            logger.info("Backend components initialized successfully")
        except Exception as e:
            logger.error(f"Backend component initialization failed: {str(e)}")
    
    def initialize_azure(self):
        """Initialize Azure services"""
        try:
            self.azure = AzureServices(self.config)
            self.doctor_manager = DoctorManager(self.azure)
            self.lab_manager = LabManager(self.azure)
            self.pharmacy_manager = PharmacyManager(self.azure)
            return True, "Azure services initialized successfully"
        except Exception as e:
            logger.error(f"Azure initialization failed: {str(e)}")
            return False, str(e)
    
    def authenticate_user(self, username, password):
        """Authenticate user"""
        try:
            success, message = self.credentials.authenticate(username, password)
            
            if success:
                self.authenticated = True
                self.current_user = username
                self.session_start = datetime.datetime.now(datetime.timezone.utc)
                self.last_activity = datetime.datetime.now(datetime.timezone.utc)
                
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
            logger.error(f"Authentication error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def logout_user(self):
        """Logout current user"""
        self.authenticated = False
        self.current_user = None
        self.session_start = None
        self.last_activity = None
        self.doctors_data = []
        self.labs_data = []
        self.pharmacies_data = []
        return {'success': True}
    
    def change_user_password(self, old_password, new_password):
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
    
    def check_user_session(self):
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
    
    def get_all_doctors(self):
        """Get all doctors"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            self.doctors_data = self.azure.get_doctor_accounts()
            
            # Process data for frontend matching testUI2.html format
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
    
    def get_all_labs(self):
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
    
    def get_all_pharmacies(self):
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
    
    def get_all_subscriptions(self):
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
    
    def get_stats(self):
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
    
    def create_new_doctor(self, doctor_data):
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
    
    def update_doctor_info(self, doctor_id, update_data):
        """Update doctor information"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            result = self.azure.update_doctor_account(doctor_id, update_data)
            return {'success': True, 'data': result}
        except Exception as e:
            logger.error(f"Failed to update doctor: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def reset_doctor_pwd(self, doctor_id):
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
    
    def export_data_to_csv(self, data_type, ids=None):
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
                            doctor.get('subscriptionStartDate', '')[:10] if doctor.get('subscriptionStartDate') else '',
                            doctor.get('subscriptionEndDate', '')[:10] if doctor.get('subscriptionEndDate') else '',
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


class UltraCleanAPI:
    """
    Ultra-clean API wrapper that ONLY has simple primitive attributes
    No complex objects stored as attributes at all
    """
    
    def __init__(self):
        # ONLY store primitive types - no objects that PyWebView might scan
        self.theme = 'dark'  # Default to dark theme
        self.is_initialized = False
        
        # Create backend service but store it globally, not as an attribute
        self._create_backend()
    
    def _create_backend(self):
        """Create backend service in global scope"""
        globals()['_backend_service'] = BackendService()
    
    def _get_backend(self):
        """Get backend service reference"""
        return globals().get('_backend_service')
    
    def _get_window(self):
        """Get window reference from global scope"""
        return globals().get('_app_window')
    
    def __eq__(self, other):
        """Prevent PyWebView comparison issues"""
        return id(self) == id(other)
    
    def __hash__(self):
        """Prevent PyWebView comparison issues"""
        return id(self)
    
    def initialize(self):
        """Initialize the application"""
        backend = self._get_backend()
        if backend:
            success, message = backend.initialize_azure()
            self.is_initialized = success
            return {'success': success, 'message': message}
        return {'success': False, 'error': 'Backend not available'}
    
    # Authentication Methods
    def login(self, username, password):
        """Authenticate user"""
        backend = self._get_backend()
        if backend:
            return backend.authenticate_user(username, password)
        return {'success': False, 'error': 'Backend not available'}
    
    def logout(self):
        """Logout current user"""
        backend = self._get_backend()
        if backend:
            return backend.logout_user()
        return {'success': True}
    
    def change_password(self, old_password, new_password):
        """Change admin password"""
        backend = self._get_backend()
        if backend:
            return backend.change_user_password(old_password, new_password)
        return {'success': False, 'error': 'Backend not available'}
    
    def check_session(self):
        """Check if session is still valid"""
        backend = self._get_backend()
        if backend:
            return backend.check_user_session()
        return {'valid': False}
    
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
        backend = self._get_backend()
        if backend:
            return backend.get_all_doctors()
        return {'success': False, 'error': 'Backend not available'}
    
    def get_labs(self):
        """Get all laboratories"""
        backend = self._get_backend()
        if backend:
            return backend.get_all_labs()
        return {'success': False, 'error': 'Backend not available'}
    
    def get_pharmacies(self):
        """Get all pharmacies"""
        backend = self._get_backend()
        if backend:
            return backend.get_all_pharmacies()
        return {'success': False, 'error': 'Backend not available'}
    
    def get_subscriptions(self):
        """Get subscription data"""
        backend = self._get_backend()
        if backend:
            return backend.get_all_subscriptions()
        return {'success': False, 'error': 'Backend not available'}
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        backend = self._get_backend()
        if backend:
            return backend.get_stats()
        return {'success': False, 'error': 'Backend not available'}
    
    def create_doctor(self, doctor_data):
        """Create new doctor account"""
        backend = self._get_backend()
        if backend:
            return backend.create_new_doctor(doctor_data)
        return {'success': False, 'error': 'Backend not available'}
    
    def update_doctor(self, doctor_id, update_data):
        """Update doctor information"""
        backend = self._get_backend()
        if backend:
            return backend.update_doctor_info(doctor_id, update_data)
        return {'success': False, 'error': 'Backend not available'}
    
    def reset_doctor_password(self, doctor_id):
        """Reset doctor password"""
        backend = self._get_backend()
        if backend:
            return backend.reset_doctor_pwd(doctor_id)
        return {'success': False, 'error': 'Backend not available'}
    
    def export_data(self, data_type, ids=None):
        """Export data to CSV"""
        backend = self._get_backend()
        if backend:
            return backend.export_data_to_csv(data_type, ids)
        return {'success': False, 'error': 'Backend not available'}
    
    def show_file_dialog(self, dialog_type='save', file_types='CSV files (*.csv)|*.csv'):
        """Show file dialog"""
        window = self._get_window()
        if window:
            if dialog_type == 'save':
                result = window.create_file_dialog(
                    webview.SAVE_DIALOG,
                    save_filename=f'export_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                    file_types=(file_types,)
                )
            else:
                result = window.create_file_dialog(
                    webview.OPEN_DIALOG,
                    file_types=(file_types,)
                )
            
            return {'success': True, 'path': result[0] if result else None}
        return {'success': False, 'error': 'Window not initialized'}


def get_html_content():
    """Get the main HTML content with minimal login interface"""
    # First try to load from files if they exist
    html_path = Path(__file__).parent / 'templates' / 'index.html'
    if html_path.exists():
        try:
            html_content = html_path.read_text(encoding='utf-8')
            
            # Replace CSS link with inline CSS if file exists
            css_path = Path(__file__).parent / 'static' / 'css' / 'styles.css'
            if css_path.exists():
                css_content = css_path.read_text(encoding='utf-8')
                html_content = html_content.replace(
                    '<link rel="stylesheet" href="static/css/styles.css">',
                    f'<style>{css_content}</style>'
                )
            
            # Replace JS link with inline JS if file exists
            js_path = Path(__file__).parent / 'static' / 'js' / 'app.js'
            if js_path.exists():
                js_content = js_path.read_text(encoding='utf-8')
                html_content = html_content.replace(
                    '<script src="static/js/app.js"></script>',
                    f'<script>{js_content}</script>'
                )
            
            return html_content
        except Exception as e:
            logger.warning(f"Failed to load HTML template files: {e}")
    
    # Return minimal embedded HTML with nearly transparent background
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
    <title>Medical Practice Management - Enhanced</title>
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet"/>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Minimal Background with Very Low Opacity */
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        html {
            background: rgba(0, 0, 0, 0.01) !important;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: rgba(0, 0, 0, 0.01) !important; 
            color: #cbd5e1 !important; 
            line-height: 1.6; 
            min-height: 100vh;
        }
        
        /* Nearly transparent login screen */
        #login-screen {
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            background: rgba(0, 0, 0, 0.01) !important; 
            padding: 20px;
        }
        
        .login-container {
            background: rgba(30, 41, 59, 0.95); 
            backdrop-filter: blur(10px); 
            border-radius: 16px;
            padding: 40px; 
            box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.1), 0 20px 25px -5px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(148, 163, 184, 0.1); 
            width: 100%; 
            max-width: 420px;
        }
        
        .login-header { text-align: center; margin-bottom: 32px; }
        .login-header h1 { color: #38bdf8; font-size: 28px; font-weight: 700; margin-bottom: 8px; }
        .login-header p { color: #94a3b8; font-size: 16px; }
        .login-form { display: flex; flex-direction: column; gap: 20px; }
        
        .form-input {
            background: rgba(30, 41, 59, 0.8); 
            border: 1px solid #475569; 
            border-radius: 8px;
            padding: 12px 16px; 
            color: #e2e8f0; 
            font-size: 16px; 
            transition: all 0.3s ease;
        }
        
        .form-input:focus { 
            outline: none; 
            border-color: #38bdf8; 
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.1); 
        }
        
        .form-input::placeholder { color: #64748b; }
        
        .login-btn {
            background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%); 
            border: none; 
            border-radius: 8px;
            padding: 12px 24px; 
            color: white; 
            font-size: 16px; 
            font-weight: 600; 
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .login-btn:hover { 
            background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%); 
            transform: translateY(-1px); 
        }
        
        .login-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
        
        .login-error {
            background: rgba(239, 68, 68, 0.1); 
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 8px; 
            padding: 12px; 
            color: #fca5a5; 
            font-size: 14px; 
            text-align: center;
        }
        
        .hidden { display: none !important; }
        
        /* Main app styling */
        #main-app {
            background: #0f172a !important;
            color: #cbd5e1 !important;
            min-height: 100vh;
        }
        
        .app-header {
            background: #1e293b;
            padding: 1rem 2rem;
            border-bottom: 1px solid #334155;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .app-title { 
            color: #38bdf8; 
            font-size: 1.5rem; 
            font-weight: 600; 
        }
        
        .app-content {
            padding: 2rem;
            background: #0f172a;
        }
        
        .success-message {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 1.5rem;
            color: #4ade80;
            text-align: center;
        }
    </style>
</head>
<body>
    <div id="login-screen">
        <div class="login-container">
            <div class="login-header">
                <h1>Medical Practice Admin</h1>
                <p>Secure Login</p>
            </div>
            <form id="login-form" class="login-form">
                <input type="text" id="username" class="form-input" placeholder="Username (admin)" required>
                <input type="password" id="password" class="form-input" placeholder="Password (admin)" required>
                <button type="submit" id="login-btn" class="login-btn">Login</button>
                <div id="login-error" class="login-error hidden"></div>
            </form>
        </div>
    </div>

    <div id="main-app" class="hidden">
        <div class="app-header">
            <h1 class="app-title">Medical Practice Management - Enhanced</h1>
            <button onclick="logout()" style="background: #ef4444; color: white; padding: 0.5rem 1rem; border: none; border-radius: 0.5rem; cursor: pointer;">
                Logout
            </button>
        </div>
        <div class="app-content">
            <div class="success-message">
                <h2 style="margin-bottom: 1rem;">✅ Application Loaded Successfully!</h2>
                <p>The minimal login interface is working correctly.</p>
                <p style="margin-top: 1rem; color: #94a3b8;">With minimal background!</p>
            </div>
        </div>
    </div>

    <script>
        document.getElementById('login-form').addEventListener('submit', function(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const loginBtn = document.getElementById('login-btn');
            const loginError = document.getElementById('login-error');
            
            if (!username || !password) {
                loginError.textContent = 'Please enter username and password';
                loginError.classList.remove('hidden');
                return;
            }
            
            loginBtn.disabled = true;
            loginBtn.textContent = 'Authenticating...';
            loginError.classList.add('hidden');
            
            setTimeout(() => {
                if (username === 'admin' && password === 'admin') {
                    document.getElementById('login-screen').classList.add('hidden');
                    document.getElementById('main-app').classList.remove('hidden');
                } else {
                    loginError.textContent = 'Invalid credentials. Try admin/admin';
                    loginError.classList.remove('hidden');
                }
                loginBtn.disabled = false;
                loginBtn.textContent = 'Login';
            }, 1000);
        });
        
        function logout() {
            document.getElementById('main-app').classList.add('hidden');
            document.getElementById('login-screen').classList.remove('hidden');
            document.getElementById('username').value = '';
            document.getElementById('password').value = '';
        }
    </script>
</body>
</html>'''


def check_gui_engines():
    """Check which GUI engines are available"""
    available_engines = []
    
    # Check for EdgeChromium (Windows only)
    if sys.platform == 'win32':
        available_engines.append('edgechromium')
    
    # Check for Qt
    for qt_lib in ['PyQt5', 'PyQt6', 'PySide2', 'PySide6']:
        try:
            __import__(qt_lib)
            available_engines.append('qt')
            break
        except ImportError:
            continue
    
    # Check for GTK (Linux/Unix)
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        try:
            import gi
            available_engines.append('gtk')
        except ImportError:
            pass
    
    # MSHTML is always available on Windows
    if sys.platform == 'win32':
        available_engines.append('mshtml')
    
    return available_engines


def main():
    """Main entry point"""
    try:
        # Create ultra-clean API instance
        api = UltraCleanAPI()
        
        # Get HTML content
        html_content = get_html_content()
        
        # Create window with transparent background
        window = webview.create_window(
            title='Medical Practice Management - Enhanced',
            html=html_content,
            frameless=True,
            transparent=True,
            vibrancy=True,
            width=420,
            height=341,
            min_size=(420, 341),
            confirm_close=True,
            text_select=True
        )

        
        # Store window reference globally (not as attribute to avoid PyWebView scanning)
        globals()['_app_window'] = window
        
        # Initialize backend after window creation
        init_result = api.initialize()
        if not init_result['success']:
            logger.error(f"Failed to initialize: {init_result.get('error')}")
            print(f"Warning: Backend initialization failed: {init_result.get('error')}")
            print("The application will start but some features may not work.")
        
        # Check available GUI engines
        available_engines = check_gui_engines()
        logger.info(f"Available GUI engines: {available_engines}")
        
        # For Windows, try engines in this order of preference
        if sys.platform == 'win32':
            engines_to_try = ['mshtml', 'qt']  # Skip edgechromium for now due to issues
        else:
            engines_to_try = available_engines if available_engines else ['qt', 'gtk']
        
        for engine in engines_to_try:
            try:
                logger.info(f"Starting application with {engine}...")
                webview.start(debug=False, gui=engine)
                break  # If successful, exit the loop
            except Exception as e:
                logger.warning(f"{engine} failed: {e}")
                continue
        else:
            # If all engines failed, try without specifying engine
            try:
                logger.info("Trying default engine...")
                webview.start(debug=False)
            except Exception as e:
                logger.error(f"All GUI engines failed: {e}")
                print("Failed to start application.")
                print("Try installing a GUI toolkit:")
                print("- pip install PyQt5")
                print("- Or pip install PyQt6")
    
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        print(f"Critical error: {e}")
        input("Press Enter to exit...")


if __name__ == '__main__':
    main()