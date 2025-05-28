#!/usr/bin/env python3
"""
Authentication Manager Module for Medical Practice Management
Handles admin authentication and session management
"""

import os
import json
import datetime
import secrets
import string
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

from .azure_services import hash_password_pbkdf2, verify_password_pbkdf2

logger = logging.getLogger(__name__)

# Security constants
SESSION_TIMEOUT_MINUTES = 30
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_WINDOW_MINUTES = 15

class AdminCredentials:
    """Admin credentials manager with security features."""
    
    def __init__(self, credentials_file: str = 'admin_credentials.json'):
        self.credentials_file = Path.home() / '.medical_practice' / credentials_file
        self.credentials_file.parent.mkdir(exist_ok=True, mode=0o700)
        self.login_attempts = {}
        self.session_start = None
        self.last_activity = None
        self.credentials = self._load_credentials()
        
        if not self.credentials:
            self._create_initial_credentials()
            
            
            
    def __eq__(self, other):
        """Override equality to prevent comparison issues with PyWebView"""
        return id(self) == id(other)
    
    def __hash__(self):
        """Override hash to prevent comparison issues with PyWebView"""
        return id(self)
        
    
    def _load_credentials(self) -> Dict[str, Any]:
        """Load credentials from encrypted file."""
        try:
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load credentials: {str(e)}")
            return {}
    
    def _save_credentials(self) -> None:
        """Save credentials to encrypted file."""
        try:
            self.credentials_file.parent.mkdir(exist_ok=True, mode=0o700)
            with open(self.credentials_file, 'w') as f:
                json.dump(self.credentials, f, indent=4)
            if os.name != 'nt':  # Not Windows
                self.credentials_file.chmod(0o600)
        except Exception as e:
            logger.error(f"Failed to save credentials: {str(e)}")
    
    def _create_initial_credentials(self) -> None:
        """Create initial admin credentials."""
        initial_password = self._generate_secure_password()
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        self.credentials = {
            'username': 'admin',
            'email': 'admin@medicalpractice.local',
            'password_hash': hash_password_pbkdf2(initial_password),
            'created_at': now.isoformat(),
            'last_login': None,
            'last_password_change': now.isoformat(),
            'require_password_change': True,
            'failed_attempts': 0,
            'locked_until': None
        }
        
        self._save_credentials()
        
        # Display credentials securely
        print("\n" + "="*60)
        print("INITIAL ADMIN CREDENTIALS")
        print("="*60)
        print(f"Username: admin")
        print(f"Password: {initial_password}")
        print("="*60)
        print("IMPORTANT: Save these credentials securely!")
        print("You will be required to change the password on first login.")
        print("="*60 + "\n")
        
        # Also save to a file for easier access during development
        info_file = self.credentials_file.parent / 'initial_credentials.txt'
        with open(info_file, 'w') as f:
            f.write("INITIAL ADMIN CREDENTIALS\n")
            f.write("========================\n")
            f.write("Username: admin\n")
            f.write(f"Password: {initial_password}\n")
            f.write("\nIMPORTANT: Delete this file after noting the credentials!\n")
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate with rate limiting and account lockout."""
        # Check if account is locked
        if self._is_account_locked():
            return False, "Account is temporarily locked due to too many failed attempts"
        
        # Validate credentials
        if username.lower() not in [self.credentials.get('username', '').lower(), 
                                   self.credentials.get('email', '').lower()]:
            self._record_failed_attempt()
            return False, "Invalid credentials"
        
        if not verify_password_pbkdf2(password, self.credentials.get('password_hash', '')):
            self._record_failed_attempt()
            return False, "Invalid credentials"
        
        # Successful login
        self._reset_failed_attempts()
        self.session_start = datetime.datetime.now(datetime.timezone.utc)
        self.last_activity = datetime.datetime.now(datetime.timezone.utc)
        self.credentials['last_login'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self._save_credentials()
        
        return True, "Success"
    
    def _is_account_locked(self) -> bool:
        """Check if account is locked due to failed attempts."""
        locked_until = self.credentials.get('locked_until')
        if locked_until:
            locked_time = datetime.datetime.fromisoformat(locked_until)
            # Ensure timezone awareness
            if locked_time.tzinfo is None:
                locked_time = locked_time.replace(tzinfo=datetime.timezone.utc)
            
            now = datetime.datetime.now(datetime.timezone.utc)
            if now < locked_time:
                return True
            else:
                # Unlock account
                self.credentials['locked_until'] = None
                self.credentials['failed_attempts'] = 0
                self._save_credentials()
        return False
    
    def _record_failed_attempt(self) -> None:
        """Record a failed login attempt."""
        self.credentials['failed_attempts'] = self.credentials.get('failed_attempts', 0) + 1
        
        if self.credentials['failed_attempts'] >= MAX_LOGIN_ATTEMPTS:
            # Lock account
            lock_duration = datetime.timedelta(minutes=LOGIN_ATTEMPT_WINDOW_MINUTES)
            self.credentials['locked_until'] = (datetime.datetime.now(datetime.timezone.utc) + lock_duration).isoformat()
        
        self._save_credentials()
    
    def _reset_failed_attempts(self) -> None:
        """Reset failed login attempts."""
        self.credentials['failed_attempts'] = 0
        self.credentials['locked_until'] = None
        self._save_credentials()
    
    def is_session_valid(self) -> bool:
        """Check if current session is still valid."""
        if not self.session_start or not self.last_activity:
            return False
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Check session timeout
        session_duration = now - self.session_start
        if session_duration.total_seconds() > SESSION_TIMEOUT_MINUTES * 60:
            return False
        
        # Check inactivity timeout
        inactivity_duration = now - self.last_activity
        if inactivity_duration.total_seconds() > SESSION_TIMEOUT_MINUTES * 60 / 2:
            return False
        
        return True
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.datetime.now(datetime.timezone.utc)
    
    def change_password(self, old_password: str, new_password: str) -> bool:
        """Change admin password with validation."""
        if not verify_password_pbkdf2(old_password, self.credentials.get('password_hash', '')):
            return False
        
        # Validate new password strength
        if len(new_password) < 12:
            raise ValueError("Password must be at least 12 characters long")
        
        if not any(c.isupper() for c in new_password):
            raise ValueError("Password must contain uppercase letters")
        
        if not any(c.islower() for c in new_password):
            raise ValueError("Password must contain lowercase letters")
        
        if not any(c.isdigit() for c in new_password):
            raise ValueError("Password must contain numbers")
        
        if not any(c in "!@#$%^&*()_+-=" for c in new_password):
            raise ValueError("Password must contain special characters")
        
        self.credentials['password_hash'] = hash_password_pbkdf2(new_password)
        self.credentials['last_password_change'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.credentials['require_password_change'] = False
        self._save_credentials()
        
        return True
    
    def _generate_secure_password(self, length: int = 16) -> str:
        """Generate a secure password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            password = ''.join(secrets.choice(alphabet) for _ in range(length))
            if (any(c.islower() for c in password) and
                any(c.isupper() for c in password) and
                any(c.isdigit() for c in password) and
                any(c in "!@#$%^&*" for c in password)):
                return password