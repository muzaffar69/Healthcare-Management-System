#!/usr/bin/env python3
"""
Azure Services Module for Medical Practice Management
Handles all Azure-related operations
"""

import os
import json
import uuid
import secrets
import string
import hashlib
import base64
import datetime
import logging
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from cryptography.fernet import Fernet

# Azure imports
import azure.identity
import azure.cosmos
import azure.storage.blob
import azure.core.exceptions
from azure.cosmos import CosmosClient, PartitionKey

logger = logging.getLogger(__name__)

# Password hashing constants
PBKDF2_ITERATIONS = 100_000
PBKDF2_SALT_LEN = 32
PBKDF2_KEY_LEN = 32

def hash_password_pbkdf2(password: str) -> str:
    """Return API-compatible pbkdf2_sha256$… string."""
    salt = os.urandom(PBKDF2_SALT_LEN)
    key = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, PBKDF2_ITERATIONS, PBKDF2_KEY_LEN
    )
    return (
        f"pbkdf2_sha256${PBKDF2_ITERATIONS}$"
        f"{base64.b64encode(salt).decode()}$"
        f"{base64.b64encode(key).decode()}"
    )

def verify_password_pbkdf2(password: str, stored: str) -> bool:
    """Validate a pbkdf2_sha256$… hash."""
    if stored.startswith("pbkdf2_sha256$"):
        _, iter_str, salt_b64, key_b64 = stored.split("$", 3)
        salt = base64.b64decode(salt_b64)
        key = base64.b64decode(key_b64)
        new = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt, int(iter_str), PBKDF2_KEY_LEN
        )
        return secrets.compare_digest(key, new)
    return False

class SecureConfig:
    """Manages configuration with encryption for sensitive data."""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self.encryption_key = self._get_or_create_key()
        self.fernet = Fernet(self.encryption_key)
        self.config = self._load_config()
        
        
    def __eq__(self, other):
        """Override equality to prevent comparison issues with PyWebView"""
        return id(self) == id(other)
    
    def __hash__(self):
        """Override hash to prevent comparison issues with PyWebView"""
        return id(self)
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key for sensitive data."""
        key_file = Path.home() / '.medical_practice' / 'key.key'
        key_file.parent.mkdir(exist_ok=True, mode=0o700)
        
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            if os.name != 'nt':  # Not Windows
                key_file.chmod(0o600)
            return key
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or environment variables."""
        # Default configuration - REPLACE WITH YOUR ACTUAL VALUES
        config = {
            "azure_tenant_id": os.getenv("AZURE_TENANT_ID", "your-tenant-id"),
            "azure_client_id": os.getenv("AZURE_CLIENT_ID", "your-client-id"),
            "azure_client_secret": os.getenv("AZURE_CLIENT_SECRET", "your-client-secret"),
            "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID", "your-subscription-id"),
            "cosmos_endpoint": os.getenv("COSMOS_ENDPOINT", "https://your-cosmos.documents.azure.com:443/"),
            "cosmos_key": os.getenv("COSMOS_KEY", "your-cosmos-key"),
            "cosmos_database": os.getenv("COSMOS_DATABASE", "medical_practice"),
            "cosmos_users_container": os.getenv("COSMOS_USERS_CONTAINER", "users"),
            "cosmos_patients_container": os.getenv("COSMOS_PATIENTS_CONTAINER", "patients"),
            "storage_account_name": os.getenv("STORAGE_ACCOUNT_NAME", "your-storage"),
            "storage_account_key": os.getenv("STORAGE_ACCOUNT_KEY", "your-storage-key"),
            "default_subscription_period": int(os.getenv("DEFAULT_SUBSCRIPTION_PERIOD", "365"))
        }
        
        # Load from config file if exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                logger.error(f"Failed to load config file: {e}")
        
        return config
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate configuration and return status with errors."""
        errors = []
        required_fields = [
            'azure_tenant_id', 'azure_client_id', 'azure_client_secret',
            'subscription_id', 'cosmos_endpoint', 'cosmos_key', 'cosmos_database'
        ]
        
        for field in required_fields:
            if not self.config.get(field) or self.config[field].startswith('your-'):
                errors.append(f"Missing or invalid field: {field}")
        
        # Validate URLs
        if self.config.get('cosmos_endpoint'):
            if not self.config['cosmos_endpoint'].startswith('https://'):
                errors.append("Cosmos endpoint must use HTTPS")
        
        return len(errors) == 0, errors
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Get configuration value using dictionary syntax."""
        return self.config[key]

class AzureServices:
    """Azure services for Medical Practice Management."""
    
    def __init__(self, config: SecureConfig):
        self.config = config
        self.cosmos_client = None
        self.blob_service_client = None
        self.graph_token = None
        self.graph_token_expires = None
        
        # Validate configuration
        is_valid, errors = config.validate()
        if not is_valid:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")
        
        self._initialize_clients()
    
    def __eq__(self, other):
        """Override equality to prevent comparison issues with PyWebView"""
        return id(self) == id(other)
    
    def __hash__(self):
        """Override hash to prevent comparison issues with PyWebView"""
        return id(self)
    
    
    def _initialize_clients(self):
        """Initialize Azure clients."""
        try:
            # Initialize Cosmos DB client
            self.cosmos_client = CosmosClient(
                url=self.config['cosmos_endpoint'],
                credential=self.config['cosmos_key']
            )
            
            # Initialize database and containers
            self._initialize_cosmos_db()
            
            logger.info("Azure clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure clients: {str(e)}")
            raise
    
    def _initialize_cosmos_db(self):
        """Initialize Cosmos DB database and containers."""
        try:
            database_name = self.config['cosmos_database']
            database = self.cosmos_client.create_database_if_not_exists(id=database_name)
            database_client = self.cosmos_client.get_database_client(database_name)
            
            # Create users container
            try:
                database_client.create_container_if_not_exists(
                    id=self.config['cosmos_users_container'],
                    partition_key=PartitionKey(path="/id"),
                    offer_throughput=400
                )
                logger.info(f"Container ready: {self.config['cosmos_users_container']}")
            except Exception as e:
                logger.warning(f"Container creation warning: {str(e)}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB: {str(e)}")
            raise
    
    def _get_graph_token(self) -> str:
        """Get a valid access token for Microsoft Graph API."""
        now = datetime.datetime.now()
        
        if not self.graph_token or not self.graph_token_expires or \
           (self.graph_token_expires - now).total_seconds() < 300:
            
            tenant_id = self.config['azure_tenant_id']
            client_id = self.config['azure_client_id']
            client_secret = self.config['azure_client_secret']
            
            token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
                'scope': 'https://graph.microsoft.com/.default'
            }
            
            response = requests.post(token_url, data=token_data)
            response.raise_for_status()
            
            token_response = response.json()
            self.graph_token = token_response['access_token']
            expires_in = token_response.get('expires_in', 3600)
            self.graph_token_expires = now + datetime.timedelta(seconds=expires_in)
        
        return self.graph_token
    
    def _call_graph_api(self, method: str, endpoint: str, json_data: Dict = None) -> Dict:
        """Call Microsoft Graph API."""
        try:
            token = self._get_graph_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            url = f"https://graph.microsoft.com/v1.0{endpoint}"
            
            if method.lower() == 'get':
                response = requests.get(url, headers=headers)
            elif method.lower() == 'post':
                response = requests.post(url, headers=headers, json=json_data)
            elif method.lower() == 'patch':
                response = requests.patch(url, headers=headers, json=json_data)
            elif method.lower() == 'delete':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code not in (200, 201, 204):
                logger.error(f"Graph API error: {response.status_code} - {response.text}")
                raise Exception(f"Graph API error: {response.status_code}")
            
            if response.status_code == 204 or not response.text:
                return {}
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Graph API call failed: {str(e)}")
            raise
    
    def get_doctor_accounts(self) -> List[Dict[str, Any]]:
        """Get all doctor accounts."""
        try:
            database = self.cosmos_client.get_database_client(self.config['cosmos_database'])
            users_container = database.get_container_client(self.config['cosmos_users_container'])
            
            query = "SELECT * FROM c WHERE c.role = 'doctor'"
            doctors = list(users_container.query_items(query=query, enable_cross_partition_query=True))
            
            return doctors
        except Exception as e:
            logger.error(f"Failed to get doctor accounts: {str(e)}")
            return []
    
    def get_lab_accounts(self) -> List[Dict[str, Any]]:
        """Get all lab accounts."""
        try:
            database = self.cosmos_client.get_database_client(self.config['cosmos_database'])
            users_container = database.get_container_client(self.config['cosmos_users_container'])
            
            query = "SELECT * FROM c WHERE c.role = 'laboratory'"
            labs = list(users_container.query_items(query=query, enable_cross_partition_query=True))
            
            return labs
        except Exception as e:
            logger.error(f"Failed to get lab accounts: {str(e)}")
            return []
    
    def get_pharmacy_accounts(self) -> List[Dict[str, Any]]:
        """Get all pharmacy accounts."""
        try:
            database = self.cosmos_client.get_database_client(self.config['cosmos_database'])
            users_container = database.get_container_client(self.config['cosmos_users_container'])
            
            query = "SELECT * FROM c WHERE c.role = 'pharmacy'"
            pharmacies = list(users_container.query_items(query=query, enable_cross_partition_query=True))
            
            return pharmacies
        except Exception as e:
            logger.error(f"Failed to get pharmacy accounts: {str(e)}")
            return []
    
    def create_doctor_account(self, doctor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new doctor account."""
        try:
            # Generate secure credentials
            password = self._generate_secure_password()
            hashed_password = hash_password_pbkdf2(password)
            doctor_id = str(uuid.uuid4())
            
            # Create Azure AD user (optional)
            user_id = None
            try:
                user_id = self._create_azure_ad_user(doctor_data, password)
            except Exception as e:
                logger.warning(f"Failed to create Azure AD user: {str(e)}")
            
            # Create accounts
            pharmacy_id = str(uuid.uuid4())
            lab_id = str(uuid.uuid4()) if doctor_data.get('create_lab_account', False) else None
            
            # Create doctor record
            doctor_record = self._create_doctor_record(
                doctor_id, user_id, doctor_data, hashed_password,
                pharmacy_id, lab_id
            )
            
            # Create associated accounts
            pharmacy_code = self._create_pharmacy_account(pharmacy_id, doctor_id, doctor_data)
            lab_code = None
            if lab_id:
                lab_code = self._create_lab_account(lab_id, doctor_id, doctor_data)
            
            return {
                'doctor_id': doctor_id,
                'doctor_email': doctor_data['email'],
                'doctor_password': password,
                'pharmacy_id': pharmacy_id,
                'pharmacy_code': pharmacy_code,
                'lab_id': lab_id,
                'lab_code': lab_code
            }
            
        except Exception as e:
            logger.error(f"Failed to create doctor account: {str(e)}")
            raise
    
    def _create_azure_ad_user(self, doctor_data: Dict[str, Any], password: str) -> Optional[str]:
        """Create Azure AD user account."""
        try:
            email = doctor_data['email']
            display_name = f"{doctor_data['first_name']} {doctor_data['last_name']}"
            
            # Get default domain
            tenant_info = self._call_graph_api('get', '/organization')
            verified_domains = tenant_info.get('value', [{}])[0].get('verifiedDomains', [])
            
            default_domain = None
            for domain in verified_domains:
                if domain.get('isDefault', False):
                    default_domain = domain.get('name')
                    break
            
            if not default_domain and verified_domains:
                default_domain = verified_domains[0].get('name')
            
            if not default_domain:
                raise Exception("No verified domains found in tenant")
            
            username = email.split('@')[0] if '@' in email else email
            user_principal_name = f"{username}@{default_domain}"
            
            user_data = {
                "accountEnabled": True,
                "displayName": display_name,
                "mailNickname": doctor_data['first_name'].lower(),
                "userPrincipalName": user_principal_name,
                "passwordProfile": {
                    "forceChangePasswordNextSignIn": True,
                    "password": password
                }
            }
            
            user = self._call_graph_api('post', '/users', user_data)
            return user.get('id')
        except Exception as e:
            logger.error(f"Failed to create Azure AD user: {str(e)}")
            raise
    
    def _create_doctor_record(self, doctor_id: str, user_id: Optional[str],
                            doctor_data: Dict[str, Any], hashed_password: str,
                            pharmacy_id: str, lab_id: Optional[str]) -> Dict[str, Any]:
        """Create doctor record in Cosmos DB."""
        subscription_period = self.config.get('default_subscription_period', 365)
        display_name = f"{doctor_data['first_name']} {doctor_data['last_name']}"
        
        now = datetime.datetime.now(datetime.timezone.utc)
        subscription_end = now + datetime.timedelta(days=subscription_period)
        
        doctor_record = {
            'id': doctor_id,
            'userId': user_id,
            'email': doctor_data['email'],
            'firstName': doctor_data['first_name'],
            'lastName': doctor_data['last_name'],
            'displayName': display_name,
            'role': 'doctor',
            'speciality': doctor_data.get('speciality', ''),
            'phoneNumber': doctor_data.get('phone_number', ''),
            'address': doctor_data.get('address', ''),
            'isActive': True,
            'hasPharmacyAccount': True,
            'hasLabAccount': lab_id is not None,
            'pharmacyAccountId': pharmacy_id,
            'labAccountId': lab_id,
            'pharmacyAccountActive': True,
            'labAccountActive': lab_id is not None,
            'subscriptionStartDate': now.isoformat(),
            'subscriptionEndDate': subscription_end.isoformat(),
            'createdAt': now.isoformat(),
            'updatedAt': now.isoformat(),
            'settings': {},
            'password_hash': hashed_password,
            'force_password_change_on_next_login': True
        }
        
        database = self.cosmos_client.get_database_client(self.config['cosmos_database'])
        users_container = database.get_container_client(self.config['cosmos_users_container'])
        users_container.create_item(body=doctor_record)
        
        return doctor_record
    
    def _create_pharmacy_account(self, pharmacy_id: str, doctor_id: str,
                               doctor_data: Dict[str, Any]) -> str:
        """Create pharmacy account."""
        display_name = f"{doctor_data['first_name']} {doctor_data['last_name']}"
        pharmacy_code = self._generate_access_code()
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        pharmacy_record = {
            'id': pharmacy_id,
            'doctorId': doctor_id,
            'name': f"{display_name}'s Pharmacy",
            'email': f"pharmacy-{doctor_id[:8]}@example.com",
            'role': 'pharmacy',
            'accessCode': pharmacy_code,
            'isActive': True,
            'createdAt': now.isoformat(),
            'updatedAt': now.isoformat()
        }
        
        database = self.cosmos_client.get_database_client(self.config['cosmos_database'])
        users_container = database.get_container_client(self.config['cosmos_users_container'])
        users_container.create_item(body=pharmacy_record)
        
        return pharmacy_code
    
    def _create_lab_account(self, lab_id: str, doctor_id: str,
                          doctor_data: Dict[str, Any]) -> str:
        """Create lab account."""
        display_name = f"{doctor_data['first_name']} {doctor_data['last_name']}"
        lab_code = self._generate_access_code()
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        lab_record = {
            'id': lab_id,
            'doctorId': doctor_id,
            'name': f"{display_name}'s Laboratory",
            'email': f"lab-{doctor_id[:8]}@example.com",
            'role': 'laboratory',
            'accessCode': lab_code,
            'isActive': True,
            'createdAt': now.isoformat(),
            'updatedAt': now.isoformat()
        }
        
        database = self.cosmos_client.get_database_client(self.config['cosmos_database'])
        users_container = database.get_container_client(self.config['cosmos_users_container'])
        users_container.create_item(body=lab_record)
        
        return lab_code
    
    def update_doctor_account(self, doctor_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a doctor account."""
        try:
            database = self.cosmos_client.get_database_client(self.config['cosmos_database'])
            users_container = database.get_container_client(self.config['cosmos_users_container'])
            
            doctor_record = users_container.read_item(item=doctor_id, partition_key=doctor_id)
            
            for key, value in update_data.items():
                if key in doctor_record:
                    doctor_record[key] = value
            
            doctor_record['updatedAt'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            updated_record = users_container.replace_item(item=doctor_id, body=doctor_record)
            
            # Update Azure AD if necessary
            if doctor_record.get('userId') and any(key in update_data for key in ['firstName', 'lastName', 'email']):
                try:
                    self._update_azure_ad_user(doctor_record['userId'], update_data)
                except Exception as e:
                    logger.warning(f"Failed to update Azure AD user: {str(e)}")
            
            return updated_record
        except Exception as e:
            logger.error(f"Failed to update doctor account: {str(e)}")
            raise
    
    def _update_azure_ad_user(self, user_id: str, update_data: Dict[str, Any]) -> None:
        """Update Azure AD user information."""
        try:
            user_data = {}
            
            if 'displayName' in update_data:
                user_data['displayName'] = update_data['displayName']
            elif 'firstName' in update_data or 'lastName' in update_data:
                first_name = update_data.get('firstName', '')
                last_name = update_data.get('lastName', '')
                user_data['displayName'] = f"{first_name} {last_name}"
            
            if 'email' in update_data:
                user_data['userPrincipalName'] = update_data['email']
                user_data['mail'] = update_data['email']
            
            if user_data:
                self._call_graph_api('patch', f'/users/{user_id}', user_data)
        except Exception as e:
            logger.warning(f"Failed to update Azure AD user: {str(e)}")
    
    def reset_doctor_password(self, doctor_id: str) -> Optional[str]:
        """Reset doctor password."""
        try:
            database = self.cosmos_client.get_database_client(self.config['cosmos_database'])
            users_container = database.get_container_client(self.config['cosmos_users_container'])
            
            doctor_record = users_container.read_item(item=doctor_id, partition_key=doctor_id)
            new_password = self._generate_secure_password()
            
            # Update password in database
            doctor_record['password_hash'] = hash_password_pbkdf2(new_password)
            doctor_record['force_password_change_on_next_login'] = True
            doctor_record['updatedAt'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            users_container.replace_item(item=doctor_id, body=doctor_record)
            
            # Update Azure AD if user exists
            azure_ad_user_id = doctor_record.get("userId")
            if azure_ad_user_id:
                try:
                    endpoint = f"/users/{azure_ad_user_id}"
                    body = {
                        "passwordProfile": {
                            "password": new_password,
                            "forceChangePasswordNextSignIn": True
                        }
                    }
                    self._call_graph_api("patch", endpoint, json_data=body)
                except Exception as e:
                    logger.warning(f"Failed to update Azure AD password: {str(e)}")
            
            logger.info(f"Password successfully reset for doctor {doctor_id}")
            return new_password
            
        except Exception as e:
            logger.error(f"Failed to reset password for doctor {doctor_id}: {e}")
            return None
    
    def _generate_secure_password(self, length: int = 16) -> str:
        """Generate a secure password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            password = ''.join(secrets.choice(alphabet) for _ in range(length))
            # Ensure password meets complexity requirements
            if (any(c.islower() for c in password) and
                any(c.isupper() for c in password) and
                any(c.isdigit() for c in password) and
                any(c in "!@#$%^&*" for c in password)):
                return password
    
    def _generate_access_code(self, length: int = 8) -> str:
        """Generate an access code."""
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))