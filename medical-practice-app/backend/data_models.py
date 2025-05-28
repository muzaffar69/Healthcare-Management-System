#!/usr/bin/env python3
"""
Data Models Module for Medical Practice Management
Provides data managers for doctors, labs, and pharmacies
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class BaseManager:
    """Base class for data managers."""
    
    def __init__(self, azure_services):
        self.azure = azure_services
    
    def _format_datetime(self, dt_str: str) -> str:
        """Format datetime string for display."""
        if not dt_str:
            return ''
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return dt_str
    
    def _format_date(self, dt_str: str) -> str:
        """Format datetime string to date only."""
        if not dt_str:
            return ''
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except:
            return dt_str[:10] if len(dt_str) >= 10 else dt_str

class DoctorManager(BaseManager):
    """Manager for doctor-related operations."""
    
    def get_all_doctors(self) -> List[Dict[str, Any]]:
        """Get all doctors with processed data."""
        try:
            doctors = self.azure.get_doctor_accounts()
            return [self._process_doctor(doc) for doc in doctors]
        except Exception as e:
            logger.error(f"Failed to get doctors: {str(e)}")
            return []
    
    def get_doctor_by_id(self, doctor_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific doctor by ID."""
        try:
            doctors = self.azure.get_doctor_accounts()
            for doc in doctors:
                if doc.get('id') == doctor_id:
                    return self._process_doctor(doc)
            return None
        except Exception as e:
            logger.error(f"Failed to get doctor {doctor_id}: {str(e)}")
            return None
    
    def create_doctor(self, doctor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new doctor."""
        try:
            result = self.azure.create_doctor_account(doctor_data)
            return result
        except Exception as e:
            logger.error(f"Failed to create doctor: {str(e)}")
            raise
    
    def update_doctor(self, doctor_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update doctor information."""
        try:
            result = self.azure.update_doctor_account(doctor_id, update_data)
            return self._process_doctor(result)
        except Exception as e:
            logger.error(f"Failed to update doctor {doctor_id}: {str(e)}")
            raise
    
    def reset_password(self, doctor_id: str) -> Optional[str]:
        """Reset doctor password."""
        try:
            return self.azure.reset_doctor_password(doctor_id)
        except Exception as e:
            logger.error(f"Failed to reset password for doctor {doctor_id}: {str(e)}")
            raise
    
    def toggle_status(self, doctor_id: str) -> Dict[str, Any]:
        """Toggle doctor active status."""
        try:
            doctor = self.get_doctor_by_id(doctor_id)
            if not doctor:
                raise ValueError("Doctor not found")
            
            new_status = not doctor.get('isActive', False)
            update_data = {'isActive': new_status}
            
            return self.update_doctor(doctor_id, update_data)
        except Exception as e:
            logger.error(f"Failed to toggle status for doctor {doctor_id}: {str(e)}")
            raise
    
    def _process_doctor(self, doctor: Dict[str, Any]) -> Dict[str, Any]:
        """Process doctor data for display."""
        # Calculate subscription info
        subscription_info = self._calculate_subscription_info(doctor)
        
        # Process the doctor data
        processed = doctor.copy()
        processed['subscriptionInfo'] = subscription_info
        processed['createdAtFormatted'] = self._format_datetime(doctor.get('createdAt', ''))
        processed['updatedAtFormatted'] = self._format_datetime(doctor.get('updatedAt', ''))
        
        return processed
    
    def _calculate_subscription_info(self, doctor: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate subscription information."""
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
                end_dt = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            else:
                end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
            
            # Ensure timezone awareness
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
            
            # Calculate days left
            now = datetime.now(timezone.utc)
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
                'statusColor': status_color,
                'endDate': self._format_date(end_date_str),
                'startDate': self._format_date(doctor.get('subscriptionStartDate', ''))
            }
        except Exception as e:
            logger.error(f"Error calculating subscription: {e}")
            return {
                'daysLeft': None,
                'status': 'error',
                'statusText': 'Error',
                'statusColor': 'gray'
            }

class LabManager(BaseManager):
    """Manager for laboratory-related operations."""
    
    def get_all_labs(self) -> List[Dict[str, Any]]:
        """Get all laboratories."""
        try:
            labs = self.azure.get_lab_accounts()
            return [self._process_lab(lab) for lab in labs]
        except Exception as e:
            logger.error(f"Failed to get labs: {str(e)}")
            return []
    
    def get_lab_by_id(self, lab_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific lab by ID."""
        try:
            labs = self.azure.get_lab_accounts()
            for lab in labs:
                if lab.get('id') == lab_id:
                    return self._process_lab(lab)
            return None
        except Exception as e:
            logger.error(f"Failed to get lab {lab_id}: {str(e)}")
            return None
    
    def get_labs_by_doctor(self, doctor_id: str) -> List[Dict[str, Any]]:
        """Get all labs for a specific doctor."""
        try:
            labs = self.azure.get_lab_accounts()
            doctor_labs = [lab for lab in labs if lab.get('doctorId') == doctor_id]
            return [self._process_lab(lab) for lab in doctor_labs]
        except Exception as e:
            logger.error(f"Failed to get labs for doctor {doctor_id}: {str(e)}")
            return []
    
    def _process_lab(self, lab: Dict[str, Any]) -> Dict[str, Any]:
        """Process lab data for display."""
        processed = lab.copy()
        processed['createdAtFormatted'] = self._format_date(lab.get('createdAt', ''))
        processed['updatedAtFormatted'] = self._format_date(lab.get('updatedAt', ''))
        processed['statusText'] = 'Active' if lab.get('isActive') else 'Inactive'
        processed['statusColor'] = 'green' if lab.get('isActive') else 'red'
        return processed

class PharmacyManager(BaseManager):
    """Manager for pharmacy-related operations."""
    
    def get_all_pharmacies(self) -> List[Dict[str, Any]]:
        """Get all pharmacies."""
        try:
            pharmacies = self.azure.get_pharmacy_accounts()
            return [self._process_pharmacy(pharmacy) for pharmacy in pharmacies]
        except Exception as e:
            logger.error(f"Failed to get pharmacies: {str(e)}")
            return []
    
    def get_pharmacy_by_id(self, pharmacy_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific pharmacy by ID."""
        try:
            pharmacies = self.azure.get_pharmacy_accounts()
            for pharmacy in pharmacies:
                if pharmacy.get('id') == pharmacy_id:
                    return self._process_pharmacy(pharmacy)
            return None
        except Exception as e:
            logger.error(f"Failed to get pharmacy {pharmacy_id}: {str(e)}")
            return None
    
    def get_pharmacies_by_doctor(self, doctor_id: str) -> List[Dict[str, Any]]:
        """Get all pharmacies for a specific doctor."""
        try:
            pharmacies = self.azure.get_pharmacy_accounts()
            doctor_pharmacies = [p for p in pharmacies if p.get('doctorId') == doctor_id]
            return [self._process_pharmacy(p) for p in doctor_pharmacies]
        except Exception as e:
            logger.error(f"Failed to get pharmacies for doctor {doctor_id}: {str(e)}")
            return []
    
    def _process_pharmacy(self, pharmacy: Dict[str, Any]) -> Dict[str, Any]:
        """Process pharmacy data for display."""
        processed = pharmacy.copy()
        processed['createdAtFormatted'] = self._format_date(pharmacy.get('createdAt', ''))
        processed['updatedAtFormatted'] = self._format_date(pharmacy.get('updatedAt', ''))
        processed['statusText'] = 'Active' if pharmacy.get('isActive') else 'Inactive'
        processed['statusColor'] = 'green' if pharmacy.get('isActive') else 'red'
        return processed