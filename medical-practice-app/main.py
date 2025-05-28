#!/usr/bin/env python3
"""
Complete Enhanced Medical Practice Management Desktop Application
With New Doctor Creation, Proper Logout, Edit Functionality, and Database Admin Login
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

class EnhancedBackendService:
    """
    Enhanced backend service with full CRUD operations and database admin login
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
        self.current_user_data = None
        self.session_start = None
        self.last_activity = None
        
        # Data caches
        self.doctors_data = []
        self.labs_data = []
        self.pharmacies_data = []
        self.admin_users = []
        
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
            
            # Load admin users from database
            self._load_admin_users()
            
            return True, "Azure services initialized successfully"
        except Exception as e:
            logger.error(f"Azure initialization failed: {str(e)}")
            return False, str(e)
    
    def _load_admin_users(self):
        """Load admin users from the users container"""
        try:
            database = self.azure.cosmos_client.get_database_client(self.config['cosmos_database'])
            users_container = database.get_container_client(self.config['cosmos_users_container'])
            
            # Query for admin users
            query = "SELECT * FROM c WHERE c.role = 'admin'"
            admin_users = list(users_container.query_items(query=query, enable_cross_partition_query=True))
            
            self.admin_users = admin_users
            logger.info(f"Loaded {len(admin_users)} admin users from database")
            
        except Exception as e:
            logger.error(f"Failed to load admin users: {str(e)}")
            self.admin_users = []
    
    def authenticate_user(self, username, password):
        """Enhanced authentication with database admin users"""
        try:
            # First try database admin users
            if self.admin_users:
                for admin_user in self.admin_users:
                    if (admin_user.get('email', '').lower() == username.lower() or 
                        admin_user.get('username', '').lower() == username.lower()):
                        
                        # Verify password using the Azure services hash verification
                        from backend.azure_services import verify_password_pbkdf2
                        stored_hash = admin_user.get('password_hash', '')
                        
                        if verify_password_pbkdf2(password, stored_hash):
                            self.authenticated = True
                            self.current_user = username
                            self.current_user_data = admin_user
                            self.session_start = datetime.datetime.now(datetime.timezone.utc)
                            self.last_activity = datetime.datetime.now(datetime.timezone.utc)
                            
                            # Update last login in database
                            self._update_last_login(admin_user['id'])
                            
                            return {
                                'success': True,
                                'username': admin_user.get('displayName', username),
                                'email': admin_user.get('email', ''),
                                'requirePasswordChange': admin_user.get('force_password_change_on_next_login', False),
                                'lastLogin': admin_user.get('last_login', 'Never'),
                                'userType': 'database_admin'
                            }
            
            # Fallback to file-based admin authentication
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
                    'lastLogin': self.credentials.credentials.get('last_login', 'Never'),
                    'userType': 'file_admin'
                }
            else:
                return {'success': False, 'error': message}
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _update_last_login(self, user_id):
        """Update last login timestamp in database"""
        try:
            database = self.azure.cosmos_client.get_database_client(self.config['cosmos_database'])
            users_container = database.get_container_client(self.config['cosmos_users_container'])
            
            # Get user document
            user_doc = users_container.read_item(item=user_id, partition_key=user_id)
            
            # Update last login
            user_doc['last_login'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            # Save back to database
            users_container.replace_item(item=user_id, body=user_doc)
            
        except Exception as e:
            logger.error(f"Failed to update last login: {str(e)}")
    
    def logout_user(self):
        """Enhanced logout with session cleanup"""
        try:
            if self.current_user_data:
                logger.info(f"User {self.current_user} logged out")
            
            self.authenticated = False
            self.current_user = None
            self.current_user_data = None
            self.session_start = None
            self.last_activity = None
            self.doctors_data = []
            self.labs_data = []
            self.pharmacies_data = []
            
            return {'success': True, 'message': 'Logged out successfully'}
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def check_session(self):
        """Enhanced session validation"""
        if not self.authenticated:
            return {'valid': False}
        
        if self.current_user_data:
            # For database users, check session validity
            now = datetime.datetime.now(datetime.timezone.utc)
            if self.session_start:
                session_duration = now - self.session_start
                if session_duration.total_seconds() > 30 * 60:  # 30 minutes
                    return {'valid': False}
        else:
            # For file-based admin, use existing credentials check
            valid = self.credentials.is_session_valid()
            if not valid:
                return {'valid': False}
        
        # Update last activity
        self.last_activity = datetime.datetime.now(datetime.timezone.utc)
        
        return {
            'valid': True,
            'remainingMinutes': self._get_remaining_session_time(),
            'currentUser': self.current_user
        }
    
    def _get_remaining_session_time(self):
        """Get remaining session time in minutes"""
        if not self.session_start:
            return 0
        
        now = datetime.datetime.now(datetime.timezone.utc)
        elapsed = now - self.session_start
        remaining = 30 - (elapsed.total_seconds() / 60)
        return max(0, int(remaining))
    
    # Enhanced Doctor Management Methods
    def create_doctor_account(self, doctor_data):
        """Enhanced doctor creation with validation"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            # Validate required fields
            required_fields = ['first_name', 'last_name', 'email']
            for field in required_fields:
                if not doctor_data.get(field):
                    return {'success': False, 'error': f'Missing required field: {field}'}
            
            # Check if email already exists
            existing_doctors = self.doctor_manager.get_all_doctors()
            for doctor in existing_doctors:
                if doctor.get('email', '').lower() == doctor_data['email'].lower():
                    return {'success': False, 'error': 'Email already exists'}
            
            # Create doctor account
            result = self.doctor_manager.create_doctor(doctor_data)
            
            logger.info(f"Doctor account created: {doctor_data['email']}")
            
            return {
                'success': True,
                'message': 'Doctor account created successfully',
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
    
    def update_doctor_account(self, doctor_id, update_data):
        """Enhanced doctor update with field validation"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            # Validate email uniqueness if email is being updated
            if 'email' in update_data:
                existing_doctors = self.doctor_manager.get_all_doctors()
                for doctor in existing_doctors:
                    if (doctor.get('email', '').lower() == update_data['email'].lower() and 
                        doctor.get('id') != doctor_id):
                        return {'success': False, 'error': 'Email already exists'}
            
            # Update doctor
            result = self.doctor_manager.update_doctor(doctor_id, update_data)
            
            logger.info(f"Doctor updated: {doctor_id}")
            
            return {
                'success': True,
                'message': 'Doctor updated successfully',
                'data': result
            }
        except Exception as e:
            logger.error(f"Failed to update doctor: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_doctor_details(self, doctor_id):
        """Get detailed doctor information for editing"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            doctor = self.doctor_manager.get_doctor_by_id(doctor_id)
            if not doctor:
                return {'success': False, 'error': 'Doctor not found'}
            
            return {'success': True, 'data': doctor}
        except Exception as e:
            logger.error(f"Failed to get doctor details: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Enhanced Lab Management
    def update_lab_account(self, lab_id, update_data):
        """Update lab account details"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            database = self.azure.cosmos_client.get_database_client(self.config['cosmos_database'])
            users_container = database.get_container_client(self.config['cosmos_users_container'])
            
            # Get lab record
            lab_record = users_container.read_item(item=lab_id, partition_key=lab_id)
            
            # Update fields
            for key, value in update_data.items():
                if key in lab_record:
                    lab_record[key] = value
            
            lab_record['updatedAt'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            # Save updated record
            updated_record = users_container.replace_item(item=lab_id, body=lab_record)
            
            logger.info(f"Lab updated: {lab_id}")
            
            return {'success': True, 'message': 'Lab updated successfully', 'data': updated_record}
        except Exception as e:
            logger.error(f"Failed to update lab: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_lab_details(self, lab_id):
        """Get detailed lab information"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            lab = self.lab_manager.get_lab_by_id(lab_id)
            if not lab:
                return {'success': False, 'error': 'Lab not found'}
            
            return {'success': True, 'data': lab}
        except Exception as e:
            logger.error(f"Failed to get lab details: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Enhanced Pharmacy Management
    def update_pharmacy_account(self, pharmacy_id, update_data):
        """Update pharmacy account details"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            database = self.azure.cosmos_client.get_database_client(self.config['cosmos_database'])
            users_container = database.get_container_client(self.config['cosmos_users_container'])
            
            # Get pharmacy record
            pharmacy_record = users_container.read_item(item=pharmacy_id, partition_key=pharmacy_id)
            
            # Update fields
            for key, value in update_data.items():
                if key in pharmacy_record:
                    pharmacy_record[key] = value
            
            pharmacy_record['updatedAt'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            # Save updated record
            updated_record = users_container.replace_item(item=pharmacy_id, body=pharmacy_record)
            
            logger.info(f"Pharmacy updated: {pharmacy_id}")
            
            return {'success': True, 'message': 'Pharmacy updated successfully', 'data': updated_record}
        except Exception as e:
            logger.error(f"Failed to update pharmacy: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_pharmacy_details(self, pharmacy_id):
        """Get detailed pharmacy information"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            pharmacy = self.pharmacy_manager.get_pharmacy_by_id(pharmacy_id)
            if not pharmacy:
                return {'success': False, 'error': 'Pharmacy not found'}
            
            return {'success': True, 'data': pharmacy}
        except Exception as e:
            logger.error(f"Failed to get pharmacy details: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Enhanced Subscription Management
    def update_subscription(self, doctor_id, subscription_data):
        """Update doctor subscription details"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            update_data = {}
            
            if 'startDate' in subscription_data:
                update_data['subscriptionStartDate'] = subscription_data['startDate']
            
            if 'endDate' in subscription_data:
                update_data['subscriptionEndDate'] = subscription_data['endDate']
            
            if 'isActive' in subscription_data:
                update_data['isActive'] = subscription_data['isActive']
            
            result = self.doctor_manager.update_doctor(doctor_id, update_data)
            
            logger.info(f"Subscription updated for doctor: {doctor_id}")
            
            return {'success': True, 'message': 'Subscription updated successfully', 'data': result}
        except Exception as e:
            logger.error(f"Failed to update subscription: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Keep all existing methods from previous implementation
    def get_all_doctors(self):
        """Get all doctors with processed data"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            self.doctors_data = self.doctor_manager.get_all_doctors()
            
            # Process data for frontend
            doctors = []
            for doctor in self.doctors_data:
                processed_doctor = {
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
                    'createdAt': doctor.get('createdAt', ''),
                    'updatedAt': doctor.get('updatedAt', ''),
                }
                
                # Calculate subscription info
                subscription_info = self._calculate_subscription_info(doctor)
                processed_doctor['daysLeft'] = subscription_info['daysLeft']
                processed_doctor['subscriptionStatus'] = subscription_info['status']
                
                doctors.append(processed_doctor)
            
            return {'success': True, 'data': doctors}
        except Exception as e:
            logger.error(f"Failed to get doctors: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_all_labs(self):
        """Get all laboratories"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            self.labs_data = self.lab_manager.get_all_labs()
            
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
                    'createdAt': lab.get('createdAt', ''),
                    'email': lab.get('email', '')
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
            
            self.pharmacies_data = self.pharmacy_manager.get_all_pharmacies()
            
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
                    'createdAt': pharmacy.get('createdAt', ''),
                    'email': pharmacy.get('email', '')
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
                    'doctorName': doctor.get('displayName', ''),
                    'email': doctor.get('email', ''),
                    'startDate': doctor.get('subscriptionStartDate', ''),
                    'endDate': doctor.get('subscriptionEndDate', ''),
                    'daysLeft': subscription_info['daysLeft'],
                    'status': subscription_info['status'],
                    'statusText': subscription_info['statusText'],
                    'statusColor': subscription_info['statusColor']
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
            
            # Ensure we have current doctor data
            doctors_result = self.get_all_doctors()
            if not doctors_result['success']:
                return doctors_result
            
            doctors = doctors_result['data']
            
            # Calculate statistics
            total_doctors = len(doctors)
            active_subs = sum(1 for d in doctors if d['subscriptionStatus'] == 'active')
            expiring_soon = sum(1 for d in doctors if d['subscriptionStatus'] == 'warning')
            expired = sum(1 for d in doctors if d['subscriptionStatus'] == 'expired')
            
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
    
    def export_data_to_csv(self, data_type, ids=None):
        """Export data to CSV"""
        try:
            if not self.authenticated:
                return {'success': False, 'error': 'Not authenticated'}
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
            
            with open(temp_file.name, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                if data_type == 'doctors':
                    # Export doctors data
                    headers = ["ID", "Name", "Email", "Status", "Specialty", "Phone", 
                             "Pharmacy Status", "Lab Status", "Subscription Start", 
                             "Subscription End", "Days Left", "Created At"]
                    writer.writerow(headers)
                    
                    for doctor in self.doctors_data:
                        if ids and doctor.get('id') not in ids:
                            continue
                        
                        subscription_info = self._calculate_subscription_info(doctor)
                        writer.writerow([
                            doctor.get('id', ''),
                            doctor.get('displayName', ''),
                            doctor.get('email', ''),
                            'Active' if doctor.get('isActive') else 'Inactive',
                            doctor.get('speciality', ''),
                            doctor.get('phoneNumber', ''),
                            'Active' if doctor.get('pharmacyAccountActive') else 'Inactive',
                            'Active' if doctor.get('labAccountActive') else 'Not Assigned',
                            doctor.get('subscriptionStartDate', '')[:10] if doctor.get('subscriptionStartDate') else '',
                            doctor.get('subscriptionEndDate', '')[:10] if doctor.get('subscriptionEndDate') else '',
                            subscription_info['daysLeft'] if subscription_info['daysLeft'] is not None else 'N/A',
                            doctor.get('createdAt', '')[:10] if doctor.get('createdAt') else ''
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
            return {
                'daysLeft': None,
                'status': 'unknown',
                'statusText': 'Not Set',
                'statusColor': 'gray'
            }
        
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
                status_text = 'Expired'
                status_color = 'red'
            elif days_left <= 30:
                status = 'warning'
                status_text = 'Expiring Soon'
                status_color = 'yellow'
            else:
                status = 'active'
                status_text = 'Active'
                status_color = 'green'
            
            return {
                'daysLeft': days_left,
                'status': status,
                'statusText': status_text,
                'statusColor': status_color
            }
        except Exception as e:
            logger.error(f"Error calculating subscription: {e}")
            return {
                'daysLeft': None,
                'status': 'error',
                'statusText': 'Error',
                'statusColor': 'gray'
            }

class CompleteAPI:
    """
    Complete API wrapper with all enhanced functionality
    """
    
    def __init__(self):
        self.theme = 'dark'
        self.is_initialized = False
        self._create_backend()
    
    def _create_backend(self):
        """Create enhanced backend service"""
        globals()['_backend_service'] = EnhancedBackendService()
    
    def _get_backend(self):
        """Get backend service reference"""
        return globals().get('_backend_service')
    
    def _get_window(self):
        """Get window reference from global scope"""
        return globals().get('_app_window')
    
    def __eq__(self, other):
        return id(self) == id(other)
    
    def __hash__(self):
        return id(self)
    
    # System Methods
    def initialize(self):
        """Initialize the application"""
        backend = self._get_backend()
        if backend:
            success, message = backend.initialize_azure()
            self.is_initialized = success
            return {'success': success, 'message': message}
        return {'success': False, 'error': 'Backend not available'}
    
    # Enhanced Authentication Methods
    def login(self, username, password):
        """Enhanced login with database admin support"""
        logger.info(f"API login called with username: {username}")
        backend = self._get_backend()
        if backend:
            result = backend.authenticate_user(username, password)
            logger.info(f"Login result: {result}")
            return result
        return {'success': False, 'error': 'Backend not available'}
    
    def logout(self):
        """Enhanced logout"""
        backend = self._get_backend()
        if backend:
            return backend.logout_user()
        return {'success': True}
    
    def check_session(self):
        """Enhanced session check"""
        backend = self._get_backend()
        if backend:
            return backend.check_session()
        return {'valid': False}
    
    # Enhanced Doctor Management
    def get_doctors(self):
        """Get all doctors"""
        backend = self._get_backend()
        if backend:
            return backend.get_all_doctors()
        return {'success': False, 'error': 'Backend not available'}
    
    def create_doctor(self, doctor_data):
        """Create new doctor account"""
        backend = self._get_backend()
        if backend:
            return backend.create_doctor_account(doctor_data)
        return {'success': False, 'error': 'Backend not available'}
    
    def update_doctor(self, doctor_id, update_data):
        """Update doctor information"""
        backend = self._get_backend()
        if backend:
            return backend.update_doctor_account(doctor_id, update_data)
        return {'success': False, 'error': 'Backend not available'}
    
    def get_doctor_details(self, doctor_id):
        """Get detailed doctor information"""
        backend = self._get_backend()
        if backend:
            return backend.get_doctor_details(doctor_id)
        return {'success': False, 'error': 'Backend not available'}
    
    def reset_doctor_password(self, doctor_id):
        """Reset doctor password"""
        backend = self._get_backend()
        if backend:
            return backend.reset_doctor_password(doctor_id)
        return {'success': False, 'error': 'Backend not available'}
    
    # Enhanced Lab Management
    def get_labs(self):
        """Get all laboratories"""
        backend = self._get_backend()
        if backend:
            return backend.get_all_labs()
        return {'success': False, 'error': 'Backend not available'}
    
    def update_lab(self, lab_id, update_data):
        """Update lab information"""
        backend = self._get_backend()
        if backend:
            return backend.update_lab_account(lab_id, update_data)
        return {'success': False, 'error': 'Backend not available'}
    
    def get_lab_details(self, lab_id):
        """Get detailed lab information"""
        backend = self._get_backend()
        if backend:
            return backend.get_lab_details(lab_id)
        return {'success': False, 'error': 'Backend not available'}
    
    # Enhanced Pharmacy Management
    def get_pharmacies(self):
        """Get all pharmacies"""
        backend = self._get_backend()
        if backend:
            return backend.get_all_pharmacies()
        return {'success': False, 'error': 'Backend not available'}
    
    def update_pharmacy(self, pharmacy_id, update_data):
        """Update pharmacy information"""
        backend = self._get_backend()
        if backend:
            return backend.update_pharmacy_account(pharmacy_id, update_data)
        return {'success': False, 'error': 'Backend not available'}
    
    def get_pharmacy_details(self, pharmacy_id):
        """Get detailed pharmacy information"""
        backend = self._get_backend()
        if backend:
            return backend.get_pharmacy_details(pharmacy_id)
        return {'success': False, 'error': 'Backend not available'}
    
    # Enhanced Subscription Management
    def get_subscriptions(self):
        """Get subscription data"""
        backend = self._get_backend()
        if backend:
            return backend.get_all_subscriptions()
        return {'success': False, 'error': 'Backend not available'}
    
    def update_subscription(self, doctor_id, subscription_data):
        """Update subscription information"""
        backend = self._get_backend()
        if backend:
            return backend.update_subscription(doctor_id, subscription_data)
        return {'success': False, 'error': 'Backend not available'}
    
    # Dashboard and Export (keeping existing methods)
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        backend = self._get_backend()
        if backend:
            return backend.get_dashboard_stats()
        return {'success': False, 'error': 'Backend not available'}
    
    def export_data(self, data_type, ids=None):
        """Export data to CSV"""
        backend = self._get_backend()
        if backend:
            return backend.export_data_to_csv(data_type, ids)
        return {'success': False, 'error': 'Backend not available'}
    
    def get_theme(self):
        """Get current theme"""
        return {'theme': self.theme}
    
    def set_theme(self, theme):
        """Set application theme"""
        self.theme = theme
        return {'success': True, 'theme': theme}

def get_enhanced_html_content():
    """Get the complete HTML with all enhanced features"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
    <title>Medical Practice Management - Enhanced with Full Features</title>
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet"/>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0f172a !important; 
            color: #cbd5e1 !important; 
            line-height: 1.6; 
            min-height: 100vh;
        }
        
        .material-icons { vertical-align: middle; }
        
        /* Login Screen */
        #login-screen {
            min-height: 100vh; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            background: #0f172a; 
            padding: 20px;
        }
        
        .login-container {
            background: #1e293b; 
            border-radius: 16px;
            padding: 40px; 
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
            border: 1px solid #334155; 
            width: 100%; 
            max-width: 420px;
        }
        
        .login-header { text-align: center; margin-bottom: 32px; }
        .login-header h1 { color: #38bdf8; font-size: 28px; font-weight: 700; margin-bottom: 8px; }
        .login-header p { color: #94a3b8; font-size: 16px; }
        .login-form { display: flex; flex-direction: column; gap: 20px; }
        
        .form-input {
            background: #334155; 
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
        
        /* Tab content visibility */
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        /* Loading spinner */
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Context Menu */
        .context-menu {
            position: absolute;
            background: rgba(30, 41, 59, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 8px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            display: none;
            min-width: 180px;
        }
        
        .context-menu-item {
            padding: 12px 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 12px;
            color: #e2e8f0;
            font-size: 14px;
            transition: all 0.2s ease;
        }
        
        .context-menu-item:hover {
            background: rgba(56, 189, 248, 0.1);
            color: #38bdf8;
        }
        
        /* Modal Styles */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(5px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .modal-content {
            background: #1e293b;
            border-radius: 12px;
            padding: 24px;
            width: 90%;
            max-width: 500px;
            max-height: 90vh;
            overflow-y: auto;
            border: 1px solid #334155;
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 12px;
            border-bottom: 1px solid #334155;
        }
        
        .modal-title {
            color: #38bdf8;
            font-size: 20px;
            font-weight: 600;
        }
        
        .modal-close {
            background: none;
            border: none;
            color: #94a3b8;
            cursor: pointer;
            font-size: 24px;
            padding: 4px;
        }
        
        .modal-close:hover {
            color: #e2e8f0;
        }
        
        .form-group {
            margin-bottom: 16px;
        }
        
        .form-label {
            display: block;
            color: #e2e8f0;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 6px;
        }
        
        .form-select {
            background: #334155;
            border: 1px solid #475569;
            border-radius: 8px;
            padding: 12px 16px;
            color: #e2e8f0;
            font-size: 16px;
            width: 100%;
            transition: all 0.3s ease;
        }
        
        .form-select:focus {
            outline: none;
            border-color: #38bdf8;
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.1);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #0ea5e9 0%, #38bdf8 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-primary:hover {
            background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%);
            transform: translateY(-1px);
        }
        
        .btn-secondary {
            background: #334155;
            color: #e2e8f0;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-secondary:hover {
            background: #475569;
        }
        
        .status-active {
            background: #15803d;
            color: #86efac;
            padding: 4px 8px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .status-inactive {
            background: #b91c1c;
            color: #fca5a5;
            padding: 4px 8px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .account-active { color: #4ade80; }
        .account-inactive { color: #94a3b8; }
        
        .table-container {
            background: #1e293b;
            border-radius: 12px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .table-header {
            background: #334155;
            padding: 16px;
            border-bottom: 1px solid #475569;
        }
        
        .table-row:hover {
            background: rgba(51, 65, 85, 0.5);
        }
        
        .stats-card {
            background: #1e293b;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        .stats-card-sky { border-left: 4px solid #0ea5e9; }
        .stats-card-green { border-left: 4px solid #22c55e; }
        .stats-card-yellow { border-left: 4px solid #eab308; }
        .stats-card-red { border-left: 4px solid #ef4444; }
        
        /* Logout button specific styling */
        .logout-btn {
            background: #dc2626;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .logout-btn:hover {
            background: #b91c1c;
            transform: translateY(-1px);
        }
    </style>
</head>
<body>
    <!-- Login Screen -->
    <div id="login-screen">
        <div class="login-container">
            <div class="login-header">
                <h1>Medical Practice Admin</h1>
                <p>Database Admin Login</p>
            </div>
            <form id="login-form" class="login-form">
                <input type="text" id="username" class="form-input" placeholder="Email or Username" required>
                <input type="password" id="password" class="form-input" placeholder="Password" required>
                <button type="submit" id="login-btn" class="login-btn">Login</button>
                <div id="login-error" class="login-error hidden"></div>
            </form>
        </div>
    </div>

    <!-- Main Application -->
    <div id="main-app" class="hidden" style="min-height: 100vh; display: flex; flex-direction: column; background: #0f172a;">
        <!-- Header -->
        <header style="background: #1e293b; padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #334155;">
            <h1 style="color: #38bdf8; font-size: 20px; font-weight: 600;">Medical Practice Management - Enhanced</h1>
            <div style="display: flex; align-items: center; gap: 16px;">
                <span id="current-user-display" style="color: #94a3b8; font-size: 14px;">Welcome, Admin</span>
                <button id="logout-btn" class="logout-btn">
                    <span class="material-icons" style="font-size: 16px; vertical-align: middle; margin-right: 4px;">logout</span>
                    Logout
                </button>
            </div>
        </header>

        <!-- Toolbar -->
        <div style="background: #1e293b; padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #334155;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <button id="refresh-btn" class="btn-primary" style="display: flex; align-items: center; gap: 8px;">
                    <span class="material-icons" style="font-size: 18px;">refresh</span>
                    Refresh
                </button>
                <button id="new-doctor-btn" class="btn-primary" style="display: flex; align-items: center; gap: 8px;">
                    <span class="material-icons" style="font-size: 18px;">add</span>
                    New Doctor
                </button>
                <button id="export-btn" class="btn-secondary" style="display: flex; align-items: center; gap: 8px;">
                    <span class="material-icons" style="font-size: 18px;">upload_file</span>
                    Export
                </button>
            </div>
            <div style="position: relative;">
                <span class="material-icons" style="position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #64748b; font-size: 20px;">search</span>
                <input id="global-search" style="background: #334155; border: 1px solid #475569; border-radius: 8px; padding: 8px 8px 8px 40px; color: #e2e8f0; width: 288px;" placeholder="Global search... (Ctrl+F)" type="text"/>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <nav style="background: #1e293b; padding: 0 24px; display: flex; border-bottom: 1px solid #334155;">
            <a data-tab="doctors" class="tab-link" style="display: flex; align-items: center; padding: 12px 20px; color: #38bdf8; font-weight: 500; text-decoration: none; border-bottom: 2px solid #38bdf8; cursor: pointer;">
                <span class="material-icons" style="margin-right: 8px; font-size: 20px;">person</span> Doctors
            </a>
            <a data-tab="laboratories" class="tab-link" style="display: flex; align-items: center; padding: 12px 20px; color: #94a3b8; font-weight: 500; text-decoration: none; cursor: pointer;">
                <span class="material-icons" style="margin-right: 8px; font-size: 20px;">science</span> Laboratories
            </a>
            <a data-tab="pharmacies" class="tab-link" style="display: flex; align-items: center; padding: 12px 20px; color: #94a3b8; font-weight: 500; text-decoration: none; cursor: pointer;">
                <span class="material-icons" style="margin-right: 8px; font-size: 20px;">local_pharmacy</span> Pharmacies
            </a>
            <a data-tab="subscriptions" class="tab-link" style="display: flex; align-items: center; padding: 12px 20px; color: #94a3b8; font-weight: 500; text-decoration: none; cursor: pointer;">
                <span class="material-icons" style="margin-right: 8px; font-size: 20px;">subscriptions</span> Subscriptions
            </a>
            <a data-tab="dashboard" class="tab-link" style="display: flex; align-items: center; padding: 12px 20px; color: #94a3b8; font-weight: 500; text-decoration: none; cursor: pointer;">
                <span class="material-icons" style="margin-right: 8px; font-size: 20px;">dashboard</span> Dashboard
            </a>
            <a data-tab="settings" class="tab-link" style="display: flex; align-items: center; padding: 12px 20px; color: #94a3b8; font-weight: 500; text-decoration: none; cursor: pointer;">
                <span class="material-icons" style="margin-right: 8px; font-size: 20px;">settings</span> Settings
            </a>
        </nav>

        <!-- Main Content Area -->
        <main style="flex-grow: 1; padding: 24px;">
            <!-- Doctors Tab -->
            <div id="doctors-tab" class="tab-content active">
                <div class="table-container">
                    <div class="table-header" style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <button id="select-all-btn" class="btn-secondary">Select All</button>
                            <button id="bulk-actions-btn" class="btn-primary">Bulk Actions</button>
                        </div>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="position: relative;">
                                <span class="material-icons" style="position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #64748b; font-size: 16px;">search</span>
                                <input id="doctors-search" style="background: #334155; border: 1px solid #475569; border-radius: 8px; padding: 8px 8px 8px 36px; color: #e2e8f0; width: 192px;" placeholder="Search..." type="text"/>
                            </div>
                            <select id="doctors-search-field" style="background: #334155; border: 1px solid #475569; border-radius: 8px; padding: 8px 12px; color: #e2e8f0;">
                                <option>All Fields</option>
                                <option>Name</option>
                                <option>Email</option>
                                <option>ID</option>
                                <option>Specialty</option>
                            </select>
                            <button id="doctors-search-btn" class="btn-primary">Search</button>
                            <button id="doctors-clear-btn" class="btn-secondary">Clear</button>
                        </div>
                    </div>
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; color: #94a3b8; font-size: 14px;">
                            <thead style="background: #334155; color: #38bdf8; font-size: 12px; text-transform: uppercase;">
                                <tr>
                                    <th style="padding: 12px 16px; text-align: left;">ID</th>
                                    <th style="padding: 12px 16px; text-align: left;">Name</th>
                                    <th style="padding: 12px 16px; text-align: left;">Email</th>
                                    <th style="padding: 12px 16px; text-align: left;">Status</th>
                                    <th style="padding: 12px 16px; text-align: left;">Specialty</th>
                                    <th style="padding: 12px 16px; text-align: left;">Phone</th>
                                    <th style="padding: 12px 16px; text-align: left;">Pharmacy</th>
                                    <th style="padding: 12px 16px; text-align: left;">Laboratory</th>
                                    <th style="padding: 12px 16px; text-align: left;">Subscription</th>
                                    <th style="padding: 12px 16px; text-align: left;">Days Left</th>
                                </tr>
                            </thead>
                            <tbody id="doctors-table-body">
                                <!-- Table content will be populated by JavaScript -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Dashboard Tab -->
            <div id="dashboard-tab" class="tab-content">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 24px; margin-bottom: 24px;">
                    <div class="stats-card stats-card-sky">
                        <div style="color: #94a3b8; font-size: 14px; font-weight: 600; margin-bottom: 8px;">Total Doctors</div>
                        <div style="color: #38bdf8; font-size: 30px; font-weight: bold;" id="total-doctors">0</div>
                        <div style="color: #64748b; font-size: 12px;">Registered</div>
                    </div>
                    <div class="stats-card stats-card-green">
                        <div style="color: #94a3b8; font-size: 14px; font-weight: 600; margin-bottom: 8px;">Active Subscriptions</div>
                        <div style="color: #4ade80; font-size: 30px; font-weight: bold;" id="active-subscriptions">0</div>
                        <div style="color: #64748b; font-size: 12px;">Current</div>
                    </div>
                    <div class="stats-card stats-card-yellow">
                        <div style="color: #94a3b8; font-size: 14px; font-weight: 600; margin-bottom: 8px;">Expiring Soon</div>
                        <div style="color: #facc15; font-size: 30px; font-weight: bold;" id="expiring-soon">0</div>
                        <div style="color: #64748b; font-size: 12px;">Next 30 days</div>
                    </div>
                    <div class="stats-card stats-card-red">
                        <div style="color: #94a3b8; font-size: 14px; font-weight: 600; margin-bottom: 8px;">Expired</div>
                        <div style="color: #f87171; font-size: 30px; font-weight: bold;" id="expired-subscriptions">0</div>
                        <div style="color: #64748b; font-size: 12px;">Total</div>
                    </div>
                </div>
                
                <div class="table-container">
                    <div class="table-header">
                        <h2 style="color: #e2e8f0; font-size: 20px; font-weight: 600;">Recent Activity</h2>
                    </div>
                    <div style="padding: 24px;">
                        <div id="activity-log" style="display: flex; flex-direction: column; gap: 12px;">
                            <div style="display: flex; align-items: center; gap: 8px; color: #94a3b8; font-size: 14px;">
                                <span class="material-icons" style="color: #38bdf8; font-size: 16px;">info</span>
                                <span>Application initialized successfully</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Other tabs (Labs, Pharmacies, Subscriptions, Settings) -->
            <div id="laboratories-tab" class="tab-content">
                <div class="table-container">
                    <div class="table-header">
                        <h2 style="color: #e2e8f0; font-size: 20px; font-weight: 600;">Laboratories</h2>
                    </div>
                    <div style="padding: 24px;">
                        <div id="labs-content">Loading laboratories...</div>
                    </div>
                </div>
            </div>

            <div id="pharmacies-tab" class="tab-content">
                <div class="table-container">
                    <div class="table-header">
                        <h2 style="color: #e2e8f0; font-size: 20px; font-weight: 600;">Pharmacies</h2>
                    </div>
                    <div style="padding: 24px;">
                        <div id="pharmacies-content">Loading pharmacies...</div>
                    </div>
                </div>
            </div>

            <div id="subscriptions-tab" class="tab-content">
                <div class="table-container">
                    <div class="table-header">
                        <h2 style="color: #e2e8f0; font-size: 20px; font-weight: 600;">Subscriptions</h2>
                    </div>
                    <div style="padding: 24px;">
                        <div id="subscriptions-content">Loading subscriptions...</div>
                    </div>
                </div>
            </div>

            <div id="settings-tab" class="tab-content">
                <div class="table-container">
                    <div class="table-header">
                        <h2 style="color: #e2e8f0; font-size: 20px; font-weight: 600;">Settings</h2>
                    </div>
                    <div style="padding: 24px;">
                        <div style="margin-bottom: 24px;">
                            <h3 style="color: #e2e8f0; font-size: 18px; font-weight: 600; margin-bottom: 16px;">Account Settings</h3>
                            <button id="change-password-btn" class="btn-primary" style="display: flex; align-items: center; gap: 8px;">
                                <span class="material-icons" style="font-size: 18px;">lock</span>
                                Change Password
                            </button>
                        </div>
                        <div>
                            <h3 style="color: #e2e8f0; font-size: 18px; font-weight: 600; margin-bottom: 16px;">Data Management</h3>
                            <button id="export-all-btn" class="btn-primary" style="display: flex; align-items: center; gap: 8px; background: #059669;">
                                <span class="material-icons" style="font-size: 18px;">download</span>
                                Export All Data
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </main>

        <footer style="background: #1e293b; padding: 12px 24px; color: #64748b; font-size: 12px; display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #334155;">
            <div style="display: flex; align-items: center;">
                <span class="material-icons" style="color: #22c55e; margin-right: 4px; font-size: 16px;">wifi</span> Connected
            </div>
            <div style="display: flex; align-items: center; gap: 16px;">
                <span id="session-timer">Session: 29 min</span>
                <span id="record-count">0 records</span>
            </div>
        </footer>
    </div>

    <!-- Context Menu -->
    <div id="context-menu" class="context-menu">
        <div class="context-menu-item" data-action="view">
            <span class="material-icons">visibility</span>
            View Details
        </div>
        <div class="context-menu-item" data-action="edit">
            <span class="material-icons">edit</span>
            Edit
        </div>
        <div class="context-menu-item" data-action="reset-password">
            <span class="material-icons">key</span>
            Reset Password
        </div>
        <div class="context-menu-item" data-action="toggle-status">
            <span class="material-icons">toggle_on</span>
            Toggle Status
        </div>
        <div class="context-menu-item" data-action="export">
            <span class="material-icons">download</span>
            Export
        </div>
    </div>

    <!-- Modal Container -->
    <div id="modal-container"></div>

    <script>
        console.log('Loading Enhanced Medical Practice Management App...');
        
        class EnhancedMedicalPracticeApp {
            constructor() {
                this.currentTab = 'doctors';
                this.selectedDoctors = new Set();
                this.allData = {
                    doctors: [],
                    labs: [],
                    pharmacies: [],
                    subscriptions: []
                };
                this.currentFilter = 'all';
                this.sessionTimer = null;
                this.currentContextData = null;
                this.init();
            }

            async init() {
                console.log('Initializing enhanced app...');
                await this.waitForPyWebView();
                this.setupEventListeners();
                console.log('✅ Enhanced app initialized successfully');
            }

            waitForPyWebView() {
                return new Promise((resolve) => {
                    if (window.pywebview && window.pywebview.api) {
                        console.log('✅ PyWebView API ready');
                        resolve();
                    } else {
                        setTimeout(() => this.waitForPyWebView().then(resolve), 100);
                    }
                });
            }

            setupEventListeners() {
                console.log('Setting up enhanced event listeners...');
                
                // Login form
                document.getElementById('login-form')?.addEventListener('submit', (e) => this.handleLogin(e));
                
                // Enhanced logout button
                document.getElementById('logout-btn')?.addEventListener('click', () => this.handleLogout());
                
                // Navigation tabs
                document.querySelectorAll('.tab-link').forEach(link => {
                    link.addEventListener('click', (e) => {
                        e.preventDefault();
                        this.switchTab(link.dataset.tab);
                    });
                });

                // Toolbar buttons
                document.getElementById('refresh-btn')?.addEventListener('click', () => this.refreshData());
                document.getElementById('new-doctor-btn')?.addEventListener('click', () => this.showNewDoctorModal());
                document.getElementById('export-btn')?.addEventListener('click', () => this.exportCurrentView());

                // Doctors tab controls
                document.getElementById('select-all-btn')?.addEventListener('click', () => this.toggleAllSelections());
                document.getElementById('bulk-actions-btn')?.addEventListener('click', () => this.showBulkActionsMenu());
                document.getElementById('doctors-search-btn')?.addEventListener('click', () => this.filterDoctors());
                document.getElementById('doctors-clear-btn')?.addEventListener('click', () => this.clearSearch());

                // Settings
                document.getElementById('change-password-btn')?.addEventListener('click', () => this.showChangePasswordModal());
                document.getElementById('export-all-btn')?.addEventListener('click', () => this.exportAllData());

                // Search on Enter
                document.getElementById('doctors-search')?.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.filterDoctors();
                    }
                });

                // Context menu
                document.addEventListener('click', () => this.hideContextMenu());
                document.addEventListener('contextmenu', (e) => {
                    if (!e.target.closest('.table-row')) {
                        e.preventDefault();
                    }
                });
            }

            async handleLogin(e) {
                e.preventDefault();
                console.log('Processing enhanced login...');
                
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const loginBtn = document.getElementById('login-btn');
                const loginError = document.getElementById('login-error');
                
                if (!username || !password) {
                    this.showLoginError('Please enter username and password');
                    return;
                }
                
                this.setLoading(loginBtn, true, 'Authenticating...');
                loginError.classList.add('hidden');
                
                try {
                    const result = await window.pywebview.api.login(username, password);
                    console.log('Enhanced login result:', result);
                    
                    if (result.success) {
                        document.getElementById('login-screen').classList.add('hidden');
                        document.getElementById('main-app').classList.remove('hidden');
                        
                        // Update user display
                        const userDisplay = document.getElementById('current-user-display');
                        if (userDisplay) {
                            userDisplay.textContent = `Welcome, ${result.username}`;
                        }
                        
                        // Load initial data
                        await this.loadInitialData();
                        this.startSessionTimer();
                        this.addActivityLog(`User ${result.username} logged in successfully`);
                        this.showMessage('Welcome to Medical Practice Management!', 'success');
                        console.log('✅ Enhanced login successful');
                    } else {
                        this.showLoginError(result.error || 'Login failed');
                    }
                } catch (error) {
                    console.error('Enhanced login error:', error);
                    this.showLoginError('Login failed: ' + error.message);
                } finally {
                    this.setLoading(loginBtn, false, 'Login');
                }
            }

            async handleLogout() {
                console.log('Processing enhanced logout...');
                try {
                    const result = await window.pywebview.api.logout();
                    console.log('Logout result:', result);
                    
                    clearInterval(this.sessionTimer);
                    document.getElementById('main-app').classList.add('hidden');
                    document.getElementById('login-screen').classList.remove('hidden');
                    document.getElementById('username').value = '';
                    document.getElementById('password').value = '';
                    document.getElementById('login-error').classList.add('hidden');
                    
                    // Reset app state
                    this.allData = { doctors: [], labs: [], pharmacies: [], subscriptions: [] };
                    this.selectedDoctors.clear();
                    
                    this.showMessage('Logged out successfully', 'info');
                    console.log('✅ Enhanced logout successful');
                } catch (error) {
                    console.error('❌ Enhanced logout error:', error);
                }
            }

            setLoading(button, loading, text) {
                if (loading) {
                    button.disabled = true;
                    button.innerHTML = `<span class="loading-spinner"></span> ${text}`;
                } else {
                    button.disabled = false;
                    button.textContent = text;
                }
            }

            showLoginError(message) {
                const loginError = document.getElementById('login-error');
                if (loginError) {
                    loginError.textContent = message;
                    loginError.classList.remove('hidden');
                }
            }

            async loadInitialData() {
                console.log('📊 Loading initial data from enhanced backend...');
                try {
                    // Load all data in parallel
                    const [doctorsResult, labsResult, pharmaciesResult, dashboardResult] = await Promise.all([
                        window.pywebview.api.get_doctors(),
                        window.pywebview.api.get_labs(),
                        window.pywebview.api.get_pharmacies(),
                        window.pywebview.api.get_dashboard_stats()
                    ]);

                    if (doctorsResult.success) {
                        this.allData.doctors = doctorsResult.data;
                        this.renderDoctorsTable();
                        console.log(`✅ Loaded ${doctorsResult.data.length} doctors`);
                    }

                    if (labsResult.success) {
                        this.allData.labs = labsResult.data;
                        console.log(`✅ Loaded ${labsResult.data.length} labs`);
                    }

                    if (pharmaciesResult.success) {
                        this.allData.pharmacies = pharmaciesResult.data;
                        console.log(`✅ Loaded ${pharmaciesResult.data.length} pharmacies`);
                    }

                    if (dashboardResult.success) {
                        this.updateDashboardStats(dashboardResult.stats);
                        console.log('✅ Dashboard stats updated');
                    }

                    console.log('✅ All initial data loaded successfully');
                } catch (error) {
                    console.error('❌ Error loading initial data:', error);
                    this.showMessage('Error loading data: ' + error.message, 'error');
                }
            }

            switchTab(tabName) {
                console.log('📋 Switching to tab:', tabName);
                
                // Update tab buttons
                document.querySelectorAll('.tab-link').forEach(link => {
                    if (link.dataset.tab === tabName) {
                        link.style.color = '#38bdf8';
                        link.style.borderBottom = '2px solid #38bdf8';
                    } else {
                        link.style.color = '#94a3b8';
                        link.style.borderBottom = 'none';
                    }
                });

                // Update tab content
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                
                const tabContent = document.getElementById(`${tabName}-tab`);
                if (tabContent) {
                    tabContent.classList.add('active');
                }
                
                this.currentTab = tabName;
                
                // Load tab-specific data
                this.loadTabData(tabName);
            }

            async loadTabData(tabName) {
                try {
                    switch(tabName) {
                        case 'laboratories':
                            await this.renderLabsData();
                            break;
                        case 'pharmacies':
                            await this.renderPharmaciesData();
                            break;
                        case 'subscriptions':
                            await this.renderSubscriptionsData();
                            break;
                        case 'dashboard':
                            await this.refreshDashboardStats();
                            break;
                    }
                } catch (error) {
                    console.error(`Error loading ${tabName} data:`, error);
                }
            }

            renderDoctorsTable() {
                console.log('📊 Rendering enhanced doctors table...');
                const tbody = document.getElementById('doctors-table-body');
                if (!tbody) return;
                
                tbody.innerHTML = '';
                
                this.allData.doctors.forEach(doctor => {
                    const row = document.createElement('tr');
                    row.className = 'table-row';
                    row.style.borderBottom = '1px solid #334155';
                    row.style.transition = 'background-color 0.15s ease-in-out';
                    row.style.cursor = 'pointer';
                    row.dataset.doctorId = doctor.id;
                    row.dataset.entityType = 'doctor';
                    
                    // Add right-click context menu
                    row.addEventListener('contextmenu', (e) => {
                        e.preventDefault();
                        this.showContextMenu(e, doctor, 'doctor');
                    });
                    
                    row.innerHTML = `
                        <td style="padding: 12px 16px; color: #64748b;">${this.truncateId(doctor.id)}</td>
                        <td style="padding: 12px 16px;">${doctor.name}</td>
                        <td style="padding: 12px 16px;">${this.truncateEmail(doctor.email)}</td>
                        <td style="padding: 12px 16px;">${this.renderStatusBadge(doctor.status)}</td>
                        <td style="padding: 12px 16px;">${doctor.specialty || ''}</td>
                        <td style="padding: 12px 16px;">${doctor.phone || ''}</td>
                        <td style="padding: 12px 16px;">${this.renderAccountStatus(doctor.pharmacyStatus)}</td>
                        <td style="padding: 12px 16px;">${doctor.labStatus === 'not_assigned' ? 'Not assigned' : this.renderAccountStatus(doctor.labStatus)}</td>
                        <td style="padding: 12px 16px;">${this.formatSubscriptionInfo(doctor)}</td>
                        <td style="padding: 12px 16px;">${doctor.daysLeft ?? 'N/A'}</td>
                    `;
                    
                    tbody.appendChild(row);
                });
                
                this.updateRecordCount(this.allData.doctors.length);
                console.log(`✅ Rendered ${this.allData.doctors.length} doctors with context menus`);
            }

            // Enhanced context menu system
            showContextMenu(e, data, entityType) {
                e.preventDefault();
                this.currentContextData = { data, entityType };
                
                const menu = document.getElementById('context-menu');
                if (!menu) return;
                
                // Position the menu
                menu.style.display = 'block';
                menu.style.left = `${e.pageX}px`;
                menu.style.top = `${e.pageY}px`;
                
                // Update menu items based on entity type
                this.updateContextMenuItems(menu, entityType);
                
                // Add click handlers
                menu.querySelectorAll('.context-menu-item').forEach(item => {
                    item.onclick = () => {
                        this.handleContextMenuAction(item.dataset.action, data, entityType);
                        this.hideContextMenu();
                    };
                });
            }

            updateContextMenuItems(menu, entityType) {
                // Customize menu items based on entity type
                const items = menu.querySelectorAll('.context-menu-item');
                items.forEach(item => {
                    const action = item.dataset.action;
                    switch(action) {
                        case 'reset-password':
                            item.style.display = entityType === 'doctor' ? 'flex' : 'none';
                            break;
                        case 'toggle-status':
                            item.style.display = ['doctor', 'lab', 'pharmacy'].includes(entityType) ? 'flex' : 'none';
                            break;
                        default:
                            item.style.display = 'flex';
                    }
                });
            }

            hideContextMenu() {
                const menu = document.getElementById('context-menu');
                if (menu) {
                    menu.style.display = 'none';
                }
                this.currentContextData = null;
            }

            async handleContextMenuAction(action, data, entityType) {
                console.log(`Context menu action: ${action} on ${entityType}`, data);
                
                switch(action) {
                    case 'view':
                        this.showDetailsModal(data, entityType);
                        break;
                    case 'edit':
                        this.showEditModal(data, entityType);
                        break;
                    case 'reset-password':
                        await this.resetPassword(data.id);
                        break;
                    case 'toggle-status':
                        await this.toggleStatus(data.id, entityType);
                        break;
                    case 'export':
                        await this.exportSingleRecord(data, entityType);
                        break;
                }
            }

            // Enhanced New Doctor Modal
            showNewDoctorModal() {
                console.log('📝 Showing new doctor modal...');
                
                const modalHtml = `
                    <div class="modal-overlay" id="new-doctor-modal">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h2 class="modal-title">Create New Doctor</h2>
                                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                            </div>
                            <form id="new-doctor-form">
                                <div class="form-group">
                                    <label class="form-label">First Name *</label>
                                    <input type="text" name="first_name" class="form-input" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Last Name *</label>
                                    <input type="text" name="last_name" class="form-input" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Email *</label>
                                    <input type="email" name="email" class="form-input" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Phone Number</label>
                                    <input type="tel" name="phone_number" class="form-input">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Specialty</label>
                                    <input type="text" name="speciality" class="form-input">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Address</label>
                                    <textarea name="address" class="form-input" rows="3"></textarea>
                                </div>
                                <div class="form-group">
                                    <label style="display: flex; align-items: center; gap: 8px; color: #e2e8f0;">
                                        <input type="checkbox" name="create_lab_account" style="margin: 0;">
                                        Create Laboratory Account
                                    </label>
                                </div>
                                <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px;">
                                    <button type="button" class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                                    <button type="submit" class="btn-primary">Create Doctor</button>
                                </div>
                            </form>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                
                // Add form submit handler
                document.getElementById('new-doctor-form').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    await this.handleCreateDoctor(e);
                });
            }

            async handleCreateDoctor(e) {
                const form = e.target;
                const formData = new FormData(form);
                const submitBtn = form.querySelector('button[type="submit"]');
                
                // Prepare doctor data
                const doctorData = {
                    first_name: formData.get('first_name'),
                    last_name: formData.get('last_name'),
                    email: formData.get('email'),
                    phone_number: formData.get('phone_number') || '',
                    speciality: formData.get('speciality') || '',
                    address: formData.get('address') || '',
                    create_lab_account: formData.has('create_lab_account')
                };
                
                this.setLoading(submitBtn, true, 'Creating...');
                
                try {
                    const result = await window.pywebview.api.create_doctor(doctorData);
                    
                    if (result.success) {
                        this.showMessage('Doctor created successfully!', 'success');
                        this.addActivityLog(`New doctor created: ${doctorData.email}`);
                        
                        // Show credentials modal
                        this.showDoctorCredentialsModal(result.data);
                        
                        // Close create modal
                        document.getElementById('new-doctor-modal').remove();
                        
                        // Refresh doctors list
                        await this.refreshData();
                    } else {
                        this.showMessage('Failed to create doctor: ' + result.error, 'error');
                    }
                } catch (error) {
                    console.error('Create doctor error:', error);
                    this.showMessage('Failed to create doctor: ' + error.message, 'error');
                } finally {
                    this.setLoading(submitBtn, false, 'Create Doctor');
                }
            }

            showDoctorCredentialsModal(credentials) {
                const modalHtml = `
                    <div class="modal-overlay" id="credentials-modal">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h2 class="modal-title">Doctor Account Created</h2>
                                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                            </div>
                            <div style="padding: 16px 0;">
                                <p style="color: #4ade80; margin-bottom: 16px;">✅ Doctor account created successfully!</p>
                                <div style="background: #334155; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                                    <h3 style="color: #38bdf8; margin-bottom: 12px;">Login Credentials</h3>
                                    <p><strong>Email:</strong> ${credentials.email}</p>
                                    <p><strong>Password:</strong> <code style="background: #1e293b; padding: 4px 8px; border-radius: 4px;">${credentials.password}</code></p>
                                </div>
                                ${credentials.pharmacyCode ? `
                                <div style="background: #334155; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                                    <h3 style="color: #22c55e; margin-bottom: 12px;">Pharmacy Access</h3>
                                    <p><strong>Access Code:</strong> <code style="background: #1e293b; padding: 4px 8px; border-radius: 4px;">${credentials.pharmacyCode}</code></p>
                                </div>
                                ` : ''}
                                ${credentials.labCode ? `
                                <div style="background: #334155; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                                    <h3 style="color: #eab308; margin-bottom: 12px;">Laboratory Access</h3>
                                    <p><strong>Access Code:</strong> <code style="background: #1e293b; padding: 4px 8px; border-radius: 4px;">${credentials.labCode}</code></p>
                                </div>
                                ` : ''}
                                <p style="color: #f87171; font-size: 14px;">⚠️ Please save these credentials securely. The password cannot be recovered.</p>
                            </div>
                            <div style="display: flex; justify-content: flex-end;">
                                <button class="btn-primary" onclick="this.closest('.modal-overlay').remove()">Close</button>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', modalHtml);
            }

            // Enhanced Edit Modal System
            showEditModal(data, entityType) {
                console.log(`📝 Showing edit modal for ${entityType}`, data);
                
                switch(entityType) {
                    case 'doctor':
                        this.showEditDoctorModal(data);
                        break;
                    case 'lab':
                        this.showEditLabModal(data);
                        break;
                    case 'pharmacy':
                        this.showEditPharmacyModal(data);
                        break;
                    case 'subscription':
                        this.showEditSubscriptionModal(data);
                        break;
                }
            }

            showEditDoctorModal(doctor) {
                const modalHtml = `
                    <div class="modal-overlay" id="edit-doctor-modal">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h2 class="modal-title">Edit Doctor: ${doctor.name}</h2>
                                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                            </div>
                            <form id="edit-doctor-form">
                                <div class="form-group">
                                    <label class="form-label">Name</label>
                                    <input type="text" name="displayName" class="form-input" value="${doctor.name || ''}" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Email</label>
                                    <input type="email" name="email" class="form-input" value="${doctor.email || ''}" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Specialty</label>
                                    <input type="text" name="speciality" class="form-input" value="${doctor.specialty || ''}">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Phone</label>
                                    <input type="tel" name="phoneNumber" class="form-input" value="${doctor.phone || ''}">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Status</label>
                                    <select name="isActive" class="form-select">
                                        <option value="true" ${doctor.status === 'active' ? 'selected' : ''}>Active</option>
                                        <option value="false" ${doctor.status === 'inactive' ? 'selected' : ''}>Inactive</option>
                                    </select>
                                </div>
                                <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px;">
                                    <button type="button" class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                                    <button type="submit" class="btn-primary">Update</button>
                                </div>
                            </form>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                
                document.getElementById('edit-doctor-form').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    await this.handleUpdateDoctor(e, doctor.id);
                });
            }

            async handleUpdateDoctor(e, doctorId) {
                const form = e.target;
                const formData = new FormData(form);
                const submitBtn = form.querySelector('button[type="submit"]');
                
                const updateData = {
                    displayName: formData.get('displayName'),
                    email: formData.get('email'),
                    speciality: formData.get('speciality'),
                    phoneNumber: formData.get('phoneNumber'),
                    isActive: formData.get('isActive') === 'true'
                };
                
                this.setLoading(submitBtn, true, 'Updating...');
                
                try {
                    const result = await window.pywebview.api.update_doctor(doctorId, updateData);
                    
                    if (result.success) {
                        this.showMessage('Doctor updated successfully!', 'success');
                        this.addActivityLog(`Doctor updated: ${updateData.email}`);
                        document.getElementById('edit-doctor-modal').remove();
                        await this.refreshData();
                    } else {
                        this.showMessage('Failed to update doctor: ' + result.error, 'error');
                    }
                } catch (error) {
                    console.error('Update doctor error:', error);
                    this.showMessage('Failed to update doctor: ' + error.message, 'error');
                } finally {
                    this.setLoading(submitBtn, false, 'Update');
                }
            }

            showEditLabModal(lab) {
                const modalHtml = `
                    <div class="modal-overlay" id="edit-lab-modal">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h2 class="modal-title">Edit Laboratory: ${lab.name}</h2>
                                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                            </div>
                            <form id="edit-lab-form">
                                <div class="form-group">
                                    <label class="form-label">Name</label>
                                    <input type="text" name="name" class="form-input" value="${lab.name || ''}" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Access Code</label>
                                    <input type="text" name="accessCode" class="form-input" value="${lab.accessCode || ''}" readonly>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Status</label>
                                    <select name="isActive" class="form-select">
                                        <option value="true" ${lab.status === 'active' ? 'selected' : ''}>Active</option>
                                        <option value="false" ${lab.status === 'inactive' ? 'selected' : ''}>Inactive</option>
                                    </select>
                                </div>
                                <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px;">
                                    <button type="button" class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                                    <button type="submit" class="btn-primary">Update</button>
                                </div>
                            </form>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                
                document.getElementById('edit-lab-form').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    await this.handleUpdateLab(e, lab.id);
                });
            }

            async handleUpdateLab(e, labId) {
                const form = e.target;
                const formData = new FormData(form);
                const submitBtn = form.querySelector('button[type="submit"]');
                
                const updateData = {
                    name: formData.get('name'),
                    isActive: formData.get('isActive') === 'true'
                };
                
                this.setLoading(submitBtn, true, 'Updating...');
                
                try {
                    const result = await window.pywebview.api.update_lab(labId, updateData);
                    
                    if (result.success) {
                        this.showMessage('Laboratory updated successfully!', 'success');
                        this.addActivityLog(`Laboratory updated: ${updateData.name}`);
                        document.getElementById('edit-lab-modal').remove();
                        await this.refreshData();
                    } else {
                        this.showMessage('Failed to update laboratory: ' + result.error, 'error');
                    }
                } catch (error) {
                    console.error('Update lab error:', error);
                    this.showMessage('Failed to update laboratory: ' + error.message, 'error');
                } finally {
                    this.setLoading(submitBtn, false, 'Update');
                }
            }

            showEditPharmacyModal(pharmacy) {
                const modalHtml = `
                    <div class="modal-overlay" id="edit-pharmacy-modal">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h2 class="modal-title">Edit Pharmacy: ${pharmacy.name}</h2>
                                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                            </div>
                            <form id="edit-pharmacy-form">
                                <div class="form-group">
                                    <label class="form-label">Name</label>
                                    <input type="text" name="name" class="form-input" value="${pharmacy.name || ''}" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Access Code</label>
                                    <input type="text" name="accessCode" class="form-input" value="${pharmacy.accessCode || ''}" readonly>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Status</label>
                                    <select name="isActive" class="form-select">
                                        <option value="true" ${pharmacy.status === 'active' ? 'selected' : ''}>Active</option>
                                        <option value="false" ${pharmacy.status === 'inactive' ? 'selected' : ''}>Inactive</option>
                                    </select>
                                </div>
                                <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px;">
                                    <button type="button" class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                                    <button type="submit" class="btn-primary">Update</button>
                                </div>
                            </form>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                
                document.getElementById('edit-pharmacy-form').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    await this.handleUpdatePharmacy(e, pharmacy.id);
                });
            }

            async handleUpdatePharmacy(e, pharmacyId) {
                const form = e.target;
                const formData = new FormData(form);
                const submitBtn = form.querySelector('button[type="submit"]');
                
                const updateData = {
                    name: formData.get('name'),
                    isActive: formData.get('isActive') === 'true'
                };
                
                this.setLoading(submitBtn, true, 'Updating...');
                
                try {
                    const result = await window.pywebview.api.update_pharmacy(pharmacyId, updateData);
                    
                    if (result.success) {
                        this.showMessage('Pharmacy updated successfully!', 'success');
                        this.addActivityLog(`Pharmacy updated: ${updateData.name}`);
                        document.getElementById('edit-pharmacy-modal').remove();
                        await this.refreshData();
                    } else {
                        this.showMessage('Failed to update pharmacy: ' + result.error, 'error');
                    }
                } catch (error) {
                    console.error('Update pharmacy error:', error);
                    this.showMessage('Failed to update pharmacy: ' + error.message, 'error');
                } finally {
                    this.setLoading(submitBtn, false, 'Update');
                }
            }

            showEditSubscriptionModal(subscription) {
                const modalHtml = `
                    <div class="modal-overlay" id="edit-subscription-modal">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h2 class="modal-title">Edit Subscription: ${subscription.doctorName}</h2>
                                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                            </div>
                            <form id="edit-subscription-form">
                                <div class="form-group">
                                    <label class="form-label">Doctor</label>
                                    <input type="text" class="form-input" value="${subscription.doctorName}" readonly>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Start Date</label>
                                    <input type="date" name="startDate" class="form-input" value="${this.formatDateForInput(subscription.startDate)}">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">End Date</label>
                                    <input type="date" name="endDate" class="form-input" value="${this.formatDateForInput(subscription.endDate)}">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Status</label>
                                    <select name="isActive" class="form-select">
                                        <option value="true" ${subscription.status === 'active' ? 'selected' : ''}>Active</option>
                                        <option value="false" ${subscription.status !== 'active' ? 'selected' : ''}>Inactive</option>
                                    </select>
                                </div>
                                <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px;">
                                    <button type="button" class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                                    <button type="submit" class="btn-primary">Update</button>
                                </div>
                            </form>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                
                document.getElementById('edit-subscription-form').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    await this.handleUpdateSubscription(e, subscription.id);
                });
            }

            async handleUpdateSubscription(e, doctorId) {
                const form = e.target;
                const formData = new FormData(form);
                const submitBtn = form.querySelector('button[type="submit"]');
                
                const updateData = {
                    startDate: formData.get('startDate'),
                    endDate: formData.get('endDate'),
                    isActive: formData.get('isActive') === 'true'
                };
                
                this.setLoading(submitBtn, true, 'Updating...');
                
                try {
                    const result = await window.pywebview.api.update_subscription(doctorId, updateData);
                    
                    if (result.success) {
                        this.showMessage('Subscription updated successfully!', 'success');
                        this.addActivityLog(`Subscription updated for doctor ID: ${doctorId}`);
                        document.getElementById('edit-subscription-modal').remove();
                        await this.refreshData();
                    } else {
                        this.showMessage('Failed to update subscription: ' + result.error, 'error');
                    }
                } catch (error) {
                    console.error('Update subscription error:', error);
                    this.showMessage('Failed to update subscription: ' + error.message, 'error');
                } finally {
                    this.setLoading(submitBtn, false, 'Update');
                }
            }

            formatDateForInput(dateStr) {
                if (!dateStr) return '';
                try {
                    const date = new Date(dateStr);
                    return date.toISOString().split('T')[0];
                } catch {
                    return '';
                }
            }

            showDetailsModal(data, entityType) {
                let detailsHtml = '';
                let title = '';
                
                switch(entityType) {
                    case 'doctor':
                        title = `Doctor Details: ${data.name}`;
                        detailsHtml = `
                            <div style="display: grid; gap: 16px;">
                                <div><strong>ID:</strong> ${data.id}</div>
                                <div><strong>Name:</strong> ${data.name}</div>
                                <div><strong>Email:</strong> ${data.email}</div>
                                <div><strong>Status:</strong> ${data.status}</div>
                                <div><strong>Specialty:</strong> ${data.specialty || 'Not specified'}</div>
                                <div><strong>Phone:</strong> ${data.phone || 'Not specified'}</div>
                                <div><strong>Pharmacy Status:</strong> ${data.pharmacyStatus}</div>
                                <div><strong>Lab Status:</strong> ${data.labStatus}</div>
                                <div><strong>Subscription:</strong> ${this.formatSubscriptionInfo(data)}</div>
                                <div><strong>Days Left:</strong> ${data.daysLeft ?? 'N/A'}</div>
                            </div>
                        `;
                        break;
                    case 'lab':
                        title = `Laboratory Details: ${data.name}`;
                        detailsHtml = `
                            <div style="display: grid; gap: 16px;">
                                <div><strong>ID:</strong> ${data.id}</div>
                                <div><strong>Name:</strong> ${data.name}</div>
                                <div><strong>Doctor:</strong> ${data.doctorName}</div>
                                <div><strong>Status:</strong> ${data.status}</div>
                                <div><strong>Access Code:</strong> <code style="background: #334155; padding: 4px 8px; border-radius: 4px;">${data.accessCode}</code></div>
                                <div><strong>Created:</strong> ${this.formatDate(data.createdAt)}</div>
                            </div>
                        `;
                        break;
                    case 'pharmacy':
                        title = `Pharmacy Details: ${data.name}`;
                        detailsHtml = `
                            <div style="display: grid; gap: 16px;">
                                <div><strong>ID:</strong> ${data.id}</div>
                                <div><strong>Name:</strong> ${data.name}</div>
                                <div><strong>Doctor:</strong> ${data.doctorName}</div>
                                <div><strong>Status:</strong> ${data.status}</div>
                                <div><strong>Access Code:</strong> <code style="background: #334155; padding: 4px 8px; border-radius: 4px;">${data.accessCode}</code></div>
                                <div><strong>Created:</strong> ${this.formatDate(data.createdAt)}</div>
                            </div>
                        `;
                        break;
                }
                
                const modalHtml = `
                    <div class="modal-overlay" id="details-modal">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h2 class="modal-title">${title}</h2>
                                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                            </div>
                            <div style="padding: 16px 0; color: #e2e8f0;">
                                ${detailsHtml}
                            </div>
                            <div style="display: flex; justify-content: flex-end;">
                                <button class="btn-primary" onclick="this.closest('.modal-overlay').remove()">Close</button>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', modalHtml);
            }

            async resetPassword(doctorId) {
                if (!confirm('Are you sure you want to reset this doctor\'s password?')) {
                    return;
                }
                
                try {
                    const result = await window.pywebview.api.reset_doctor_password(doctorId);
                    
                    if (result.success) {
                        const modalHtml = `
                            <div class="modal-overlay" id="password-reset-modal">
                                <div class="modal-content">
                                    <div class="modal-header">
                                        <h2 class="modal-title">Password Reset</h2>
                                        <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                                    </div>
                                    <div style="padding: 16px 0;">
                                        <p style="color: #4ade80; margin-bottom: 16px;">✅ Password reset successfully!</p>
                                        <div style="background: #334155; padding: 16px; border-radius: 8px;">
                                            <p><strong>New Password:</strong></p>
                                            <code style="background: #1e293b; padding: 8px 12px; border-radius: 4px; display: block; margin-top: 8px;">${result.password}</code>
                                        </div>
                                        <p style="color: #f87171; font-size: 14px; margin-top: 16px;">⚠️ Please save this password securely. It cannot be recovered.</p>
                                    </div>
                                    <div style="display: flex; justify-content: flex-end;">
                                        <button class="btn-primary" onclick="this.closest('.modal-overlay').remove()">Close</button>
                                    </div>
                                </div>
                            </div>
                        `;
                        
                        document.body.insertAdjacentHTML('beforeend', modalHtml);
                        this.showMessage('Password reset successfully', 'success');
                        this.addActivityLog(`Password reset for doctor ID: ${doctorId}`);
                    } else {
                        this.showMessage('Failed to reset password: ' + result.error, 'error');
                    }
                } catch (error) {
                    console.error('Reset password error:', error);
                    this.showMessage('Failed to reset password: ' + error.message, 'error');
                }
            }

            async toggleStatus(entityId, entityType) {
                const entityName = entityType.charAt(0).toUpperCase() + entityType.slice(1);
                
                if (!confirm(`Are you sure you want to toggle the status of this ${entityType}?`)) {
                    return;
                }
                
                try {
                    let result;
                    switch(entityType) {
                        case 'doctor':
                            result = await window.pywebview.api.toggle_doctor_status(entityId);
                            break;
                        default:
                            this.showMessage(`Status toggle for ${entityType} not implemented yet`, 'warning');
                            return;
                    }
                    
                    if (result && result.success) {
                        this.showMessage(`${entityName} status toggled successfully`, 'success');
                        this.addActivityLog(`${entityName} status toggled: ${entityId}`);
                        await this.refreshData();
                    } else {
                        this.showMessage(`Failed to toggle ${entityType} status: ` + (result?.error || 'Unknown error'), 'error');
                    }
                } catch (error) {
                    console.error(`Toggle ${entityType} status error:`, error);
                    this.showMessage(`Failed to toggle ${entityType} status: ` + error.message, 'error');
                }
            }

            async exportSingleRecord(data, entityType) {
                try {
                    const result = await window.pywebview.api.export_data(entityType + 's', [data.id]);
                    
                    if (result.success) {
                        const link = document.createElement('a');
                        link.href = 'data:text/csv;base64,' + result.data;
                        link.download = result.filename;
                        link.click();
                        this.showMessage(`${entityType} data exported successfully`, 'success');
                    } else {
                        this.showMessage('Export failed: ' + result.error, 'error');
                    }
                } catch (error) {
                    console.error('Export error:', error);
                    this.showMessage('Export failed: ' + error.message, 'error');
                }
            }

            // Enhanced Labs Data Rendering with Context Menus
            async renderLabsData() {
                const labsContent = document.getElementById('labs-content');
                if (!labsContent) return;
                
                if (this.allData.labs.length === 0) {
                    labsContent.innerHTML = '<p style="color: #94a3b8;">No laboratories found.</p>';
                    return;
                }

                let html = '<div style="display: grid; gap: 16px;">';
                this.allData.labs.forEach(lab => {
                    html += `
                        <div class="lab-card" style="background: #334155; border-radius: 8px; padding: 16px; border-left: 4px solid #38bdf8; cursor: pointer;" 
                             data-lab-id="${lab.id}" data-entity-type="lab">
                            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                                <h4 style="color: #e2e8f0; font-size: 16px; font-weight: 600;">${lab.name}</h4>
                                <span class="${lab.status === 'active' ? 'status-active' : 'status-inactive'}">${lab.status}</span>
                            </div>
                            <div style="color: #94a3b8; font-size: 14px;">
                                <p><strong>Doctor:</strong> ${lab.doctorName}</p>
                                <p><strong>Access Code:</strong> <code style="background: #1e293b; padding: 2px 6px; border-radius: 4px;">${lab.accessCode}</code></p>
                                <p><strong>Created:</strong> ${this.formatDate(lab.createdAt)}</p>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                
                labsContent.innerHTML = html;
                
                // Add context menu to lab cards
                document.querySelectorAll('.lab-card').forEach(card => {
                    card.addEventListener('contextmenu', (e) => {
                        e.preventDefault();
                        const labId = card.dataset.labId;
                        const lab = this.allData.labs.find(l => l.id === labId);
                        if (lab) {
                            this.showContextMenu(e, lab, 'lab');
                        }
                    });
                });
            }

            // Enhanced Pharmacy Data Rendering with Context Menus
            async renderPharmaciesData() {
                const pharmaciesContent = document.getElementById('pharmacies-content');
                if (!pharmaciesContent) return;
                
                if (this.allData.pharmacies.length === 0) {
                    pharmaciesContent.innerHTML = '<p style="color: #94a3b8;">No pharmacies found.</p>';
                    return;
                }

                let html = '<div style="display: grid; gap: 16px;">';
                this.allData.pharmacies.forEach(pharmacy => {
                    html += `
                        <div class="pharmacy-card" style="background: #334155; border-radius: 8px; padding: 16px; border-left: 4px solid #22c55e; cursor: pointer;" 
                             data-pharmacy-id="${pharmacy.id}" data-entity-type="pharmacy">
                            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                                <h4 style="color: #e2e8f0; font-size: 16px; font-weight: 600;">${pharmacy.name}</h4>
                                <span class="${pharmacy.status === 'active' ? 'status-active' : 'status-inactive'}">${pharmacy.status}</span>
                            </div>
                            <div style="color: #94a3b8; font-size: 14px;">
                                <p><strong>Doctor:</strong> ${pharmacy.doctorName}</p>
                                <p><strong>Access Code:</strong> <code style="background: #1e293b; padding: 2px 6px; border-radius: 4px;">${pharmacy.accessCode}</code></p>
                                <p><strong>Created:</strong> ${this.formatDate(pharmacy.createdAt)}</p>
                            </div>
                        </div>
                    `;
                });
                html += '</div>';
                
                pharmaciesContent.innerHTML = html;
                
                // Add context menu to pharmacy cards
                document.querySelectorAll('.pharmacy-card').forEach(card => {
                    card.addEventListener('contextmenu', (e) => {
                        e.preventDefault();
                        const pharmacyId = card.dataset.pharmacyId;
                        const pharmacy = this.allData.pharmacies.find(p => p.id === pharmacyId);
                        if (pharmacy) {
                            this.showContextMenu(e, pharmacy, 'pharmacy');
                        }
                    });
                });
            }

            // Enhanced Subscription Data Rendering with Context Menus
            async renderSubscriptionsData() {
                const subscriptionsContent = document.getElementById('subscriptions-content');
                if (!subscriptionsContent) return;
                
                try {
                    const result = await window.pywebview.api.get_subscriptions();
                    if (!result.success) {
                        subscriptionsContent.innerHTML = `<p style="color: #f87171;">Error: ${result.error}</p>`;
                        return;
                    }

                    if (result.data.length === 0) {
                        subscriptionsContent.innerHTML = '<p style="color: #94a3b8;">No subscriptions found.</p>';
                        return;
                    }

                    let html = '<div style="display: grid; gap: 16px;">';
                    result.data.forEach(sub => {
                        const borderColor = sub.status === 'active' ? '#22c55e' : 
                                          sub.status === 'warning' ? '#eab308' : '#ef4444';
                        
                        html += `
                            <div class="subscription-card" style="background: #334155; border-radius: 8px; padding: 16px; border-left: 4px solid ${borderColor}; cursor: pointer;" 
                                 data-subscription-id="${sub.id}" data-entity-type="subscription">
                                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                                    <h4 style="color: #e2e8f0; font-size: 16px; font-weight: 600;">${sub.doctorName}</h4>
                                    <span class="status-${sub.status === 'warning' ? 'warning' : sub.status === 'active' ? 'active' : 'inactive'}">${sub.statusText}</span>
                                </div>
                                <div style="color: #94a3b8; font-size: 14px;">
                                    <p><strong>Email:</strong> ${sub.email}</p>
                                    <p><strong>Period:</strong> ${this.formatDate(sub.startDate)} - ${this.formatDate(sub.endDate)}</p>
                                    <p><strong>Days Remaining:</strong> ${sub.daysLeft ?? 'N/A'}</p>
                                </div>
                            </div>
                        `;
                    });
                    html += '</div>';
                    
                    subscriptionsContent.innerHTML = html;
                    
                    // Add context menu to subscription cards
                    document.querySelectorAll('.subscription-card').forEach(card => {
                        card.addEventListener('contextmenu', (e) => {
                            e.preventDefault();
                            const subscriptionId = card.dataset.subscriptionId;
                            const subscription = result.data.find(s => s.id === subscriptionId);
                            if (subscription) {
                                this.showContextMenu(e, subscription, 'subscription');
                            }
                        });
                    });
                } catch (error) {
                    console.error('Error rendering subscriptions:', error);
                    subscriptionsContent.innerHTML = `<p style="color: #f87171;">Error loading subscriptions: ${error.message}</p>`;
                }
            }

            // Keep all existing methods from previous implementation
            async refreshDashboardStats() {
                try {
                    const result = await window.pywebview.api.get_dashboard_stats();
                    if (result.success) {
                        this.updateDashboardStats(result.stats);
                    }
                } catch (error) {
                    console.error('Error refreshing dashboard stats:', error);
                }
            }

            updateDashboardStats(stats) {
                document.getElementById('total-doctors').textContent = stats.totalDoctors;
                document.getElementById('active-subscriptions').textContent = stats.activeSubscriptions;
                document.getElementById('expiring-soon').textContent = stats.expiringSoon;
                document.getElementById('expired-subscriptions').textContent = stats.expired;
            }

            async refreshData() {
                console.log('🔄 Refreshing all data...');
                this.showMessage('Refreshing data...', 'info');
                
                try {
                    await this.loadInitialData();
                    await this.loadTabData(this.currentTab);
                    this.addActivityLog('Data refreshed by user');
                    this.showMessage('Data refreshed successfully', 'success');
                } catch (error) {
                    console.error('Error refreshing data:', error);
                    this.showMessage('Error refreshing data: ' + error.message, 'error');
                }
            }

            async filterDoctors() {
                const searchText = document.getElementById('doctors-search')?.value.toLowerCase() || '';
                const searchField = document.getElementById('doctors-search-field')?.value || 'All Fields';
                
                if (!searchText) {
                    this.renderDoctorsTable();
                    return;
                }
                
                const filtered = this.allData.doctors.filter(doctor => {
                    if (searchField === 'All Fields') {
                        return Object.values(doctor).some(val => 
                            String(val).toLowerCase().includes(searchText)
                        );
                    } else {
                        const fieldMap = {
                            'Name': 'name',
                            'Email': 'email',
                            'ID': 'id',
                            'Specialty': 'specialty'
                        };
                        const field = fieldMap[searchField];
                        return doctor[field]?.toLowerCase().includes(searchText);
                    }
                });
                
                this.renderFilteredDoctors(filtered);
                this.showMessage(`Found ${filtered.length} matching doctors`, 'info');
            }

            renderFilteredDoctors(doctors) {
                const tbody = document.getElementById('doctors-table-body');
                if (!tbody) return;
                
                tbody.innerHTML = '';
                doctors.forEach(doctor => {
                    const row = document.createElement('tr');
                    row.className = 'table-row';
                    row.style.borderBottom = '1px solid #334155';
                    row.style.cursor = 'pointer';
                    row.dataset.doctorId = doctor.id;
                    row.dataset.entityType = 'doctor';
                    
                    // Add context menu
                    row.addEventListener('contextmenu', (e) => {
                        e.preventDefault();
                        this.showContextMenu(e, doctor, 'doctor');
                    });
                    
                    row.innerHTML = `
                        <td style="padding: 12px 16px; color: #64748b;">${this.truncateId(doctor.id)}</td>
                        <td style="padding: 12px 16px;">${doctor.name}</td>
                        <td style="padding: 12px 16px;">${this.truncateEmail(doctor.email)}</td>
                        <td style="padding: 12px 16px;">${this.renderStatusBadge(doctor.status)}</td>
                        <td style="padding: 12px 16px;">${doctor.specialty || ''}</td>
                        <td style="padding: 12px 16px;">${doctor.phone || ''}</td>
                        <td style="padding: 12px 16px;">${this.renderAccountStatus(doctor.pharmacyStatus)}</td>
                        <td style="padding: 12px 16px;">${doctor.labStatus === 'not_assigned' ? 'Not assigned' : this.renderAccountStatus(doctor.labStatus)}</td>
                        <td style="padding: 12px 16px;">${this.formatSubscriptionInfo(doctor)}</td>
                        <td style="padding: 12px 16px;">${doctor.daysLeft ?? 'N/A'}</td>
                    `;
                    tbody.appendChild(row);
                });
                
                this.updateRecordCount(doctors.length);
            }

            clearSearch() {
                document.getElementById('doctors-search').value = '';
                this.renderDoctorsTable();
            }

            startSessionTimer() {
                this.sessionTimer = setInterval(async () => {
                    try {
                        const result = await window.pywebview.api.check_session();
                        if (result && result.valid) {
                            document.getElementById('session-timer').textContent = `Session: ${result.remainingMinutes} min`;
                        } else {
                            clearInterval(this.sessionTimer);
                            this.showMessage('Session expired. Please log in again.', 'warning');
                            this.handleLogout();
                        }
                    } catch (error) {
                        console.error('Session check error:', error);
                    }
                }, 60000);
                
                // Initial update
                this.checkSession();
            }

            async checkSession() {
                try {
                    const result = await window.pywebview.api.check_session();
                    if (result && result.valid) {
                        document.getElementById('session-timer').textContent = `Session: ${result.remainingMinutes} min`;
                    }
                } catch (error) {
                    console.error('Session check error:', error);
                }
            }

            toggleAllSelections() {
                const allSelected = this.selectedDoctors.size === this.allData.doctors.length;
                
                if (allSelected) {
                    this.selectedDoctors.clear();
                    this.showMessage('All doctors deselected', 'info');
                } else {
                    this.allData.doctors.forEach(doctor => {
                        this.selectedDoctors.add(doctor.id);
                    });
                    this.showMessage('All doctors selected', 'success');
                }
            }

            showBulkActionsMenu() {
                this.showMessage(`Bulk actions for ${this.selectedDoctors.size} selected doctors - Coming soon`, 'info');
            }

            async exportCurrentView() {
                try {
                    const dataType = this.currentTab === 'doctors' ? 'doctors' : 
                                   this.currentTab === 'laboratories' ? 'labs' :
                                   this.currentTab === 'pharmacies' ? 'pharmacies' : 'doctors';
                    
                    const result = await window.pywebview.api.export_data(dataType);
                    if (result.success) {
                        const link = document.createElement('a');
                        link.href = 'data:text/csv;base64,' + result.data;
                        link.download = result.filename;
                        link.click();
                        this.showMessage('Data exported successfully', 'success');
                    } else {
                        this.showMessage('Export failed: ' + result.error, 'error');
                    }
                } catch (error) {
                    console.error('Export error:', error);
                    this.showMessage('Export failed: ' + error.message, 'error');
                }
            }

            async exportAllData() {
                try {
                    const result = await window.pywebview.api.export_data('doctors');
                    if (result.success) {
                        const link = document.createElement('a');
                        link.href = 'data:text/csv;base64,' + result.data;
                        link.download = result.filename;
                        link.click();
                        this.showMessage('All data exported successfully', 'success');
                    } else {
                        this.showMessage('Export failed: ' + result.error, 'error');
                    }
                } catch (error) {
                    console.error('Export error:', error);
                    this.showMessage('Export failed: ' + error.message, 'error');
                }
            }

            showChangePasswordModal() {
                const modalHtml = `
                    <div class="modal-overlay" id="change-password-modal">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h2 class="modal-title">Change Password</h2>
                                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                            </div>
                            <form id="change-password-form">
                                <div class="form-group">
                                    <label class="form-label">Current Password</label>
                                    <input type="password" name="currentPassword" class="form-input" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">New Password</label>
                                    <input type="password" name="newPassword" class="form-input" required>
                                    <small style="color: #94a3b8; font-size: 12px;">Minimum 12 characters with uppercase, lowercase, numbers, and special characters</small>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Confirm New Password</label>
                                    <input type="password" name="confirmPassword" class="form-input" required>
                                </div>
                                <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px;">
                                    <button type="button" class="btn-secondary" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
                                    <button type="submit" class="btn-primary">Change Password</button>
                                </div>
                            </form>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                
                document.getElementById('change-password-form').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    await this.handleChangePassword(e);
                });
            }

            async handleChangePassword(e) {
                const form = e.target;
                const formData = new FormData(form);
                const submitBtn = form.querySelector('button[type="submit"]');
                
                const currentPassword = formData.get('currentPassword');
                const newPassword = formData.get('newPassword');
                const confirmPassword = formData.get('confirmPassword');
                
                if (newPassword !== confirmPassword) {
                    this.showMessage('Passwords do not match', 'error');
                    return;
                }
                
                this.setLoading(submitBtn, true, 'Changing...');
                
                try {
                    const result = await window.pywebview.api.change_password(currentPassword, newPassword);
                    
                    if (result.success) {
                        this.showMessage('Password changed successfully', 'success');
                        this.addActivityLog('Password changed by user');
                        document.getElementById('change-password-modal').remove();
                    } else {
                        this.showMessage('Password change failed: ' + result.error, 'error');
                    }
                } catch (error) {
                    console.error('Password change error:', error);
                    this.showMessage('Password change failed: ' + error.message, 'error');
                } finally {
                    this.setLoading(submitBtn, false, 'Change Password');
                }
            }

            // Helper methods (keeping existing ones)
            renderStatusBadge(status) {
                const statusClass = status === 'active' ? 'status-active' : 'status-inactive';
                return `<span class="${statusClass}">${status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown'}</span>`;
            }

            renderAccountStatus(status) {
                if (status === 'active') {
                    return '<span class="account-active"><span class="material-icons" style="font-size: 16px;">check</span> Active</span>';
                } else {
                    return '<span class="account-inactive"><span class="material-icons" style="font-size: 16px;">close</span> Inactive</span>';
                }
            }

            truncateId(id) {
                return id ? id.substring(0, 12) + '...' : '';
            }

            truncateEmail(email) {
                if (!email) return '';
                if (email.length <= 15) return email;
                return email.substring(0, 12) + '...';
            }

            formatSubscriptionInfo(doctor) {
                if (!doctor.subscriptionStart || !doctor.subscriptionEnd) {
                    return 'Not Set';
                }
                
                const startDate = this.formatDate(doctor.subscriptionStart);
                return `${startDate} to...`;
            }

            formatDate(dateStr) {
                if (!dateStr) return '';
                try {
                    const date = new Date(dateStr);
                    return date.toLocaleDateString();
                } catch {
                    return dateStr;
                }
            }

            updateRecordCount(count) {
                const recordCountEl = document.getElementById('record-count');
                if (recordCountEl) {
                    recordCountEl.textContent = `${count} records`;
                }
            }

            addActivityLog(message) {
                const activityLog = document.getElementById('activity-log');
                if (!activityLog) return;
                
                const entry = document.createElement('div');
                entry.style.display = 'flex';
                entry.style.alignItems = 'center';
                entry.style.gap = '8px';
                entry.style.color = '#94a3b8';
                entry.style.fontSize = '14px';
                entry.innerHTML = `
                    <span class="material-icons" style="color: #38bdf8; font-size: 16px;">info</span>
                    <span>${message} - ${new Date().toLocaleTimeString()}</span>
                `;
                
                activityLog.insertBefore(entry, activityLog.firstChild);
                while (activityLog.children.length > 10) {
                    activityLog.removeChild(activityLog.lastChild);
                }
            }

            showMessage(message, type = 'info') {
                console.log(`${type.toUpperCase()}: ${message}`);
                
                const toast = document.createElement('div');
                const colors = {
                    success: '#059669',
                    error: '#dc2626',
                    info: '#0284c7',
                    warning: '#d97706'
                };
                
                const icons = {
                    success: 'check_circle',
                    error: 'error',
                    info: 'info',
                    warning: 'warning'
                };
                
                toast.style.cssText = `
                    position: fixed;
                    top: 16px;
                    right: 16px;
                    background: ${colors[type]};
                    color: white;
                    padding: 12px 24px;
                    border-radius: 8px;
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
                    z-index: 1000;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    transform: translateX(100%);
                    opacity: 0;
                    transition: all 0.3s ease;
                `;
                
                toast.innerHTML = `
                    <span class="material-icons" style="font-size: 18px;">${icons[type]}</span>
                    <span>${message}</span>
                `;
                
                document.body.appendChild(toast);
                
                setTimeout(() => {
                    toast.style.transform = 'translateX(0)';
                    toast.style.opacity = '1';
                }, 10);
                
                setTimeout(() => {
                    toast.style.transform = 'translateX(100%)';
                    toast.style.opacity = '0';
                    setTimeout(() => toast.remove(), 300);
                }, 3000);
            }
        }

        // Initialize enhanced app when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {
            console.log('DOM loaded, initializing Enhanced Medical Practice App...');
            window.app = new EnhancedMedicalPracticeApp();
        });
        
        console.log('✅ Enhanced Medical Practice Management loaded successfully');
    </script>
</body>
</html>'''

def check_gui_engines():
    """Check which GUI engines are available"""
    available_engines = []
    
    if sys.platform == 'win32':
        available_engines.append('edgechromium')
    
    for qt_lib in ['PyQt5', 'PyQt6', 'PySide2', 'PySide6']:
        try:
            __import__(qt_lib)
            available_engines.append('qt')
            break
        except ImportError:
            continue
    
    if sys.platform.startswith('linux') or sys.platform == 'darwin':
        try:
            import gi
            available_engines.append('gtk')
        except ImportError:
            pass
    
    if sys.platform == 'win32':
        available_engines.append('mshtml')
    
    return available_engines

def main():
    """Main entry point"""
    try:
        # Create enhanced API instance
        api = CompleteAPI()
        
        # Get enhanced HTML content
        html_content = get_enhanced_html_content()
        
        # Create window
        window = webview.create_window(
            title='Medical Practice Management - Enhanced with Full Features',
            html=html_content,
            js_api=api,
            width=1400,
            height=900,
            min_size=(1000, 700),
            confirm_close=True,
            text_select=True,
            resizable=True
        )
        
        # Store window reference globally
        globals()['_app_window'] = window
        
        # Initialize backend
        init_result = api.initialize()
        if not init_result['success']:
            logger.error(f"Failed to initialize: {init_result.get('error')}")
            print(f"Warning: Backend initialization failed: {init_result.get('error')}")
        
        # Check available GUI engines
        available_engines = check_gui_engines()
        logger.info(f"Available GUI engines: {available_engines}")
        
        # Start with preferred engine
        if sys.platform == 'win32':
            engines_to_try = ['edgechromium', 'qt']
        else:
            engines_to_try = available_engines if available_engines else ['qt', 'gtk']
        
        for engine in engines_to_try:
            try:
                logger.info(f"Starting application with {engine}...")
                webview.start(debug=True, gui=engine)
                break
            except Exception as e:
                logger.warning(f"{engine} failed: {e}")
                continue
        else:
            try:
                logger.info("Trying default engine...")
                webview.start(debug=True)
            except Exception as e:
                logger.error(f"All GUI engines failed: {e}")
                print("Failed to start application.")
    
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        print(f"Critical error: {e}")
        input("Press Enter to exit...")

if __name__ == '__main__':
    main()