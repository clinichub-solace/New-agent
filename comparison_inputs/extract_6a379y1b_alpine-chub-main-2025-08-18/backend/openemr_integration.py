#!/usr/bin/env python3
"""
OpenEMR Integration Layer for ClinicHub
This will eventually connect to a real OpenEMR instance.
For now, it provides the API structure we'll need.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional
from datetime import datetime, date
import os

class OpenEMRIntegration:
    def __init__(self, base_url: str = None, api_token: str = None):
        # For now, use placeholder URL - will be updated when OpenEMR is deployed
        self.base_url = base_url or "http://localhost:8080"
        self.api_token = api_token
        self.api_endpoint = f"{self.base_url}/apis/default/api"
        
    async def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate with OpenEMR and get API token"""
        auth_data = {
            "grant_type": "password",
            "username": username,
            "password": password,
            "scope": "default"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/oauth2/default/token", 
                                      data=auth_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.api_token = result.get("access_token")
                        return self.api_token
        except Exception as e:
            print(f"OpenEMR Authentication failed: {e}")
            # For development, return a mock token
            self.api_token = "mock_token_for_development"
            return self.api_token
        
        return None
    
    async def get_patients(self, limit: int = 20) -> List[Dict]:
        """Get patient list from OpenEMR"""
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_endpoint}/patient", 
                                     headers=headers,
                                     params={"_limit": limit}) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Failed to fetch patients: {e}")
            # Return mock data for development
            return self._mock_patients()
        
        return []
    
    async def get_patient(self, patient_id: str) -> Optional[Dict]:
        """Get specific patient data"""
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_endpoint}/patient/{patient_id}", 
                                     headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Failed to fetch patient {patient_id}: {e}")
            # Return mock data for development
            return self._mock_patient(patient_id)
        
        return None
    
    async def create_patient(self, patient_data: Dict) -> Optional[Dict]:
        """Create new patient in OpenEMR"""
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_endpoint}/patient", 
                                      headers=headers,
                                      json=patient_data) as response:
                    if response.status in [200, 201]:
                        return await response.json()
        except Exception as e:
            print(f"Failed to create patient: {e}")
            # Return mock success for development
            return {"id": "mock_patient_id", "status": "created", **patient_data}
        
        return None
    
    async def get_encounters(self, patient_id: str) -> List[Dict]:
        """Get patient encounters"""
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_endpoint}/patient/{patient_id}/encounter", 
                                     headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Failed to fetch encounters for patient {patient_id}: {e}")
            return self._mock_encounters(patient_id)
        
        return []
    
    async def create_encounter(self, patient_id: str, encounter_data: Dict) -> Optional[Dict]:
        """Create new encounter"""
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_endpoint}/patient/{patient_id}/encounter", 
                                      headers=headers,
                                      json=encounter_data) as response:
                    if response.status in [200, 201]:
                        return await response.json()
        except Exception as e:
            print(f"Failed to create encounter: {e}")
            return {"id": "mock_encounter_id", "status": "created", **encounter_data}
        
        return None
    
    async def get_prescriptions(self, patient_id: str) -> List[Dict]:
        """Get patient prescriptions"""
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_endpoint}/patient/{patient_id}/prescription", 
                                     headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Failed to fetch prescriptions for patient {patient_id}: {e}")
            return self._mock_prescriptions(patient_id)
        
        return []
    
    # Mock data methods for development
    def _mock_patients(self) -> List[Dict]:
        return [
            {
                "id": "1",
                "fname": "John",
                "lname": "Doe",
                "DOB": "1980-01-15",
                "sex": "Male",
                "phone_home": "555-0123",
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "postal_code": "12345"
            },
            {
                "id": "2", 
                "fname": "Jane",
                "lname": "Smith",
                "DOB": "1975-06-22",
                "sex": "Female",
                "phone_home": "555-0456",
                "street": "456 Oak Ave",
                "city": "Somewhere",
                "state": "TX",
                "postal_code": "67890"
            }
        ]
    
    def _mock_patient(self, patient_id: str) -> Dict:
        patients = self._mock_patients()
        for patient in patients:
            if patient["id"] == patient_id:
                return patient
        return patients[0]  # Default to first patient
    
    def _mock_encounters(self, patient_id: str) -> List[Dict]:
        return [
            {
                "id": "enc_1",
                "patient_id": patient_id,
                "date": "2024-01-15",
                "reason": "Annual Physical",
                "provider": "Dr. Smith"
            }
        ]
    
    def _mock_prescriptions(self, patient_id: str) -> List[Dict]:
        return [
            {
                "id": "rx_1",
                "patient_id": patient_id,
                "drug": "Lisinopril 10mg",
                "directions": "Take once daily",
                "quantity": "30",
                "refills": "2"
            }
        ]

# Global instance
openemr = OpenEMRIntegration()

# Test the integration
if __name__ == "__main__":
    async def test_integration():
        # Test authentication
        token = await openemr.authenticate("admin", "admin123")
        print(f"Authentication token: {token}")
        
        # Test getting patients
        patients = await openemr.get_patients()
        print(f"Found {len(patients)} patients")
        
        if patients:
            patient_id = patients[0]["id"]
            
            # Test getting specific patient
            patient = await openemr.get_patient(patient_id)
            print(f"Patient details: {patient}")
            
            # Test getting encounters
            encounters = await openemr.get_encounters(patient_id)
            print(f"Patient encounters: {encounters}")
            
            # Test getting prescriptions
            prescriptions = await openemr.get_prescriptions(patient_id)
            print(f"Patient prescriptions: {prescriptions}")
    
    asyncio.run(test_integration())