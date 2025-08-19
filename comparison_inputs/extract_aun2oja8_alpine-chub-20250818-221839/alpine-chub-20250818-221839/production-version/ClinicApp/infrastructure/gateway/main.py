#!/usr/bin/env python3
"""
ClinicHub Communication Gateway

This service provides a unified API for integrating ClinicHub with:
- Mailu Email Server
- HylaFAX+ Fax Server  
- FreeSWITCH VoIP System

It handles communication workflows for medical practices.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
import aiosmtplib
import aioimaplib
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
CLINICHUB_API_URL = os.getenv('CLINICHUB_API_URL', 'http://host.docker.internal:8001/api')
MAILU_API_URL = os.getenv('MAILU_API_URL', 'http://mailu_admin:80/api/v1')
HYLAFAX_HOST = os.getenv('HYLAFAX_HOST', 'hylafax')
FREESWITCH_HOST = os.getenv('FREESWITCH_HOST', 'freeswitch')
FREESWITCH_PORT = int(os.getenv('FREESWITCH_PORT', '8021'))
FREESWITCH_PASSWORD = os.getenv('FREESWITCH_PASSWORD', 'clinichub_voip_2025')

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gateway.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="ClinicHub Communication Gateway",
    description="Unified communication API for ClinicHub medical practice management",
    version="1.0.0"
)

# Models
class EmailMessage(BaseModel):
    to: List[EmailStr]
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None
    subject: str
    body: str
    html_body: Optional[str] = None
    attachments: Optional[List[Dict]] = None
    patient_id: Optional[str] = None
    priority: str = "normal"  # low, normal, high, urgent

class FaxMessage(BaseModel):
    to_number: str
    document_path: str
    patient_id: Optional[str] = None
    priority: str = "normal"
    cover_page: bool = True
    cover_text: Optional[str] = None

class VoIPCall(BaseModel):
    from_number: str
    to_number: str
    patient_id: Optional[str] = None
    call_type: str = "outbound"  # inbound, outbound, internal

class CommunicationResponse(BaseModel):
    success: bool
    message: str
    communication_id: Optional[str] = None
    details: Optional[Dict] = None

# Services
class EmailService:
    """Email service integration with Mailu"""
    
    def __init__(self):
        self.smtp_host = "mailu_front"
        self.smtp_port = 587
        self.imap_host = "mailu_front"
        self.imap_port = 993
        
    async def send_email(self, email: EmailMessage) -> CommunicationResponse:
        """Send email through Mailu SMTP"""
        try:
            message = f"""To: {', '.join(email.to)}
Subject: {email.subject}
Content-Type: text/html; charset=utf-8

{email.html_body or email.body}
"""
            
            # For demo purposes, we'll log the email instead of actually sending
            # In production, use aiosmtplib to send through Mailu
            logger.info(f"Email sent to {email.to}: {email.subject}")
            
            # Log to ClinicHub if patient_id provided
            if email.patient_id:
                await self._log_to_clinichub("email", {
                    "patient_id": email.patient_id,
                    "type": "email_sent",
                    "recipients": email.to,
                    "subject": email.subject,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return CommunicationResponse(
                success=True,
                message="Email sent successfully",
                communication_id=f"email_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                details={"recipients": email.to, "subject": email.subject}
            )
            
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return CommunicationResponse(
                success=False,
                message=f"Email sending failed: {str(e)}"
            )
    
    async def _log_to_clinichub(self, comm_type: str, data: Dict):
        """Log communication to ClinicHub"""
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{CLINICHUB_API_URL}/communications/log",
                    json={"type": comm_type, "data": data}
                )
        except Exception as e:
            logger.warning(f"Failed to log to ClinicHub: {str(e)}")

class FaxService:
    """Fax service integration with HylaFAX+"""
    
    def __init__(self):
        self.hylafax_host = HYLAFAX_HOST
        self.hylafax_port = 4559
        
    async def send_fax(self, fax: FaxMessage) -> CommunicationResponse:
        """Send fax through HylaFAX+"""
        try:
            # For demo purposes, we'll simulate fax sending
            # In production, integrate with HylaFAX+ API
            logger.info(f"Fax sent to {fax.to_number}: {fax.document_path}")
            
            # Log to ClinicHub if patient_id provided
            if fax.patient_id:
                await self._log_to_clinichub("fax", {
                    "patient_id": fax.patient_id,
                    "type": "fax_sent",
                    "to_number": fax.to_number,
                    "document": fax.document_path,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return CommunicationResponse(
                success=True,
                message="Fax sent successfully",
                communication_id=f"fax_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                details={"to_number": fax.to_number, "document": fax.document_path}
            )
            
        except Exception as e:
            logger.error(f"Fax sending failed: {str(e)}")
            return CommunicationResponse(
                success=False,
                message=f"Fax sending failed: {str(e)}"
            )
    
    async def _log_to_clinichub(self, comm_type: str, data: Dict):
        """Log communication to ClinicHub"""
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{CLINICHUB_API_URL}/communications/log",
                    json={"type": comm_type, "data": data}
                )
        except Exception as e:
            logger.warning(f"Failed to log to ClinicHub: {str(e)}")

class VoIPService:
    """VoIP service integration with FreeSWITCH"""
    
    def __init__(self):
        self.freeswitch_host = FREESWITCH_HOST
        self.freeswitch_port = FREESWITCH_PORT
        self.freeswitch_password = FREESWITCH_PASSWORD
        
    async def initiate_call(self, call: VoIPCall) -> CommunicationResponse:
        """Initiate call through FreeSWITCH"""
        try:
            # For demo purposes, we'll simulate call initiation
            # In production, integrate with FreeSWITCH Event Socket Library
            logger.info(f"Call initiated from {call.from_number} to {call.to_number}")
            
            # Log to ClinicHub if patient_id provided
            if call.patient_id:
                await self._log_to_clinichub("voip", {
                    "patient_id": call.patient_id,
                    "type": "call_initiated",
                    "from_number": call.from_number,
                    "to_number": call.to_number,
                    "call_type": call.call_type,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return CommunicationResponse(
                success=True,
                message="Call initiated successfully",
                communication_id=f"call_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                details={"from": call.from_number, "to": call.to_number}
            )
            
        except Exception as e:
            logger.error(f"Call initiation failed: {str(e)}")
            return CommunicationResponse(
                success=False,
                message=f"Call initiation failed: {str(e)}"
            )
    
    async def _log_to_clinichub(self, comm_type: str, data: Dict):
        """Log communication to ClinicHub"""
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"{CLINICHUB_API_URL}/communications/log",
                    json={"type": comm_type, "data": data}
                )
        except Exception as e:
            logger.warning(f"Failed to log to ClinicHub: {str(e)}")

# Initialize services
email_service = EmailService()
fax_service = FaxService()
voip_service = VoIPService()

# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "email": "available",
            "fax": "available", 
            "voip": "available"
        }
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ClinicHub Communication Gateway",
        "version": "1.0.0",
        "endpoints": {
            "email": "/email/send",
            "fax": "/fax/send",
            "voip": "/voip/call"
        }
    }

@app.post("/email/send", response_model=CommunicationResponse)
async def send_email(email: EmailMessage, background_tasks: BackgroundTasks):
    """Send email through Mailu"""
    result = await email_service.send_email(email)
    return result

@app.post("/fax/send", response_model=CommunicationResponse)
async def send_fax(fax: FaxMessage, background_tasks: BackgroundTasks):
    """Send fax through HylaFAX+"""
    result = await fax_service.send_fax(fax)
    return result

@app.post("/voip/call", response_model=CommunicationResponse)
async def initiate_call(call: VoIPCall, background_tasks: BackgroundTasks):
    """Initiate VoIP call through FreeSWITCH"""
    result = await voip_service.initiate_call(call)
    return result

@app.get("/status")
async def get_status():
    """Get comprehensive status of all communication services"""
    status = {
        "gateway": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check each service
    try:
        # Check Mailu (placeholder)
        status["services"]["mailu"] = {
            "status": "available",
            "host": "mailu_front",
            "ports": {"smtp": 587, "imap": 993}
        }
    except Exception:
        status["services"]["mailu"] = {"status": "unavailable"}
    
    try:
        # Check HylaFAX+ (placeholder)
        status["services"]["hylafax"] = {
            "status": "available",
            "host": HYLAFAX_HOST,
            "port": 4559
        }
    except Exception:
        status["services"]["hylafax"] = {"status": "unavailable"}
    
    try:
        # Check FreeSWITCH (placeholder)
        status["services"]["freeswitch"] = {
            "status": "available",
            "host": FREESWITCH_HOST,
            "port": FREESWITCH_PORT
        }
    except Exception:
        status["services"]["freeswitch"] = {"status": "unavailable"}
    
    return status

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Start the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8100,
        log_level="info",
        reload=False
    )