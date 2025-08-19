#!/usr/bin/env python3
"""
ClinicHub Interoperability Worker
Processes domain events and handles healthcare data integration with:
- HAPI FHIR Server
- Mirth Connect (HL7/X12)
- External healthcare systems
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime

import pika
import requests
from fhirclient import client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClinicHubInteropWorker:
    """Processes ClinicHub domain events for healthcare interoperability"""
    
    def __init__(self):
        self.rabbitmq_url = os.getenv('RABBITMQ_URL')
        self.hapi_fhir_url = os.getenv('HAPI_FHIR_URL', 'http://hapi-fhir:8080/fhir')
        self.mirth_url = os.getenv('MIRTH_URL', 'https://mirth-connect:8443')
        self.mirth_username = os.getenv('MIRTH_USERNAME', 'admin')
        self.mirth_password = self._read_secret('MIRTH_PASSWORD_FILE', 'admin')
        
        # Initialize FHIR client
        self.fhir_client = None
        self._init_fhir_client()
        
        # Initialize message queue connection
        self.connection = None
        self.channel = None
        self._init_rabbitmq()
    
    def _read_secret(self, env_var: str, fallback: str = '') -> str:
        """Read secret from file or environment variable"""
        secret_file = os.getenv(env_var)
        if secret_file and os.path.exists(secret_file):
            with open(secret_file, 'r') as f:
                return f.read().strip()
        return fallback
    
    def _init_fhir_client(self):
        """Initialize HAPI FHIR client"""
        try:
            settings = {
                'app_id': 'clinichub_interop',
                'api_base': self.hapi_fhir_url
            }
            self.fhir_client = client.FHIRClient(settings=settings)
            logger.info(f"FHIR client initialized: {self.hapi_fhir_url}")
        except Exception as e:
            logger.error(f"Failed to initialize FHIR client: {e}")
    
    def _init_rabbitmq(self):
        """Initialize RabbitMQ connection"""
        try:
            # Parse connection parameters
            if self.rabbitmq_url:
                connection_params = pika.URLParameters(self.rabbitmq_url)
            else:
                connection_params = pika.ConnectionParameters(
                    host='rabbitmq',
                    port=5672,
                    virtual_host='clinichub',
                    credentials=pika.PlainCredentials('clinichub', 'changeme')
                )
            
            self.connection = pika.BlockingConnection(connection_params)
            self.channel = self.connection.channel()
            
            # Declare exchanges and queues
            self.channel.exchange_declare(exchange='clinichub.events', exchange_type='topic')
            self.channel.queue_declare(queue='interop.fhir', durable=True)
            self.channel.queue_declare(queue='interop.hl7', durable=True)
            
            # Bind queues to exchanges
            self.channel.queue_bind(exchange='clinichub.events', queue='interop.fhir', routing_key='*.created')
            self.channel.queue_bind(exchange='clinichub.events', queue='interop.fhir', routing_key='*.updated')
            self.channel.queue_bind(exchange='clinichub.events', queue='interop.hl7', routing_key='lab.*')
            
            logger.info("RabbitMQ connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize RabbitMQ: {e}")
    
    def process_fhir_event(self, ch, method, properties, body):
        """Process FHIR-related domain events"""
        try:
            event = json.loads(body.decode())
            logger.info(f"Processing FHIR event: {event['event_type']}")
            
            # Extract FHIR resource from event
            fhir_resource = event.get('data', {}).get('fhir_resource')
            if not fhir_resource:
                logger.warning("No FHIR resource found in event")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            # Send to HAPI FHIR server
            success = self._send_to_fhir_server(fhir_resource)
            
            if success:
                logger.info(f"Successfully processed FHIR event: {event['aggregate_id']}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                logger.error(f"Failed to process FHIR event: {event['aggregate_id']}")
                # Reject and requeue for retry (implement max retry logic)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                
        except Exception as e:
            logger.error(f"Error processing FHIR event: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def process_hl7_event(self, ch, method, properties, body):
        """Process HL7-related domain events"""
        try:
            event = json.loads(body.decode())
            logger.info(f"Processing HL7 event: {event['event_type']}")
            
            # Convert event to HL7 message format
            hl7_message = self._convert_to_hl7(event)
            
            if hl7_message:
                # Send to Mirth Connect for processing
                success = self._send_to_mirth(hl7_message, event['event_type'])
                
                if success:
                    logger.info(f"Successfully processed HL7 event: {event['aggregate_id']}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    logger.error(f"Failed to process HL7 event: {event['aggregate_id']}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            else:
                logger.warning(f"Could not convert event to HL7: {event['event_type']}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
        except Exception as e:
            logger.error(f"Error processing HL7 event: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def _send_to_fhir_server(self, fhir_resource: Dict[str, Any]) -> bool:
        """Send FHIR resource to HAPI FHIR server"""
        try:
            resource_type = fhir_resource.get('resourceType')
            resource_id = fhir_resource.get('id')
            
            if not resource_type or not resource_id:
                logger.error("Invalid FHIR resource: missing resourceType or id")
                return False
            
            # PUT request to create/update resource
            url = f"{self.hapi_fhir_url}/{resource_type}/{resource_id}"
            headers = {
                'Content-Type': 'application/fhir+json',
                'Accept': 'application/fhir+json'
            }
            
            response = requests.put(url, json=fhir_resource, headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                logger.info(f"FHIR resource created/updated: {resource_type}/{resource_id}")
                return True
            else:
                logger.error(f"FHIR server error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending to FHIR server: {e}")
            return False
    
    def _convert_to_hl7(self, event: Dict[str, Any]) -> str:
        """Convert domain event to HL7 v2 message"""
        # This is a simplified example - real implementation would use HL7 library
        event_type = event.get('event_type')
        
        if event_type == 'lab.order.created':
            # Create HL7 ORM (Order Message)
            return self._create_hl7_orm(event)
        elif event_type == 'patient.created':
            # Create HL7 ADT (Admit/Discharge/Transfer)
            return self._create_hl7_adt(event)
        
        return None
    
    def _create_hl7_orm(self, event: Dict[str, Any]) -> str:
        """Create HL7 ORM message for lab orders"""
        # Simplified HL7 ORM message structure
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        
        hl7_message = f"""MSH|^~\\&|CLINICHUB|CLINIC|LAB|LABSYS|{timestamp}||ORM^O01|{event['aggregate_id']}|P|2.5
PID|1||{event['data'].get('patient_id', '')}||DOE^JOHN||19800101|M
ORC|NW|{event['aggregate_id']}|{event['aggregate_id']}||IP||||{timestamp}
OBR|1|{event['aggregate_id']}|{event['aggregate_id']}|CBC^COMPLETE BLOOD COUNT"""
        
        return hl7_message
    
    def _create_hl7_adt(self, event: Dict[str, Any]) -> str:
        """Create HL7 ADT message for patient registration"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        
        hl7_message = f"""MSH|^~\\&|CLINICHUB|CLINIC|HIS|HOSPITAL|{timestamp}||ADT^A04|{event['aggregate_id']}|P|2.5
PID|1||{event['aggregate_id']}||{event['data'].get('last_name', '')}^{event['data'].get('first_name', '')}||{event['data'].get('birth_date', '')}|{event['data'].get('gender', '')}"""
        
        return hl7_message
    
    def _send_to_mirth(self, hl7_message: str, message_type: str) -> bool:
        """Send HL7 message to Mirth Connect"""
        try:
            # This would integrate with Mirth Connect's REST API
            # For now, just log the message
            logger.info(f"HL7 Message ({message_type}):\n{hl7_message}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending to Mirth: {e}")
            return False
    
    def start_consuming(self):
        """Start consuming messages from RabbitMQ"""
        if not self.channel:
            logger.error("RabbitMQ channel not initialized")
            return
        
        try:
            # Set up consumers
            self.channel.basic_consume(
                queue='interop.fhir',
                on_message_callback=self.process_fhir_event
            )
            
            self.channel.basic_consume(
                queue='interop.hl7',
                on_message_callback=self.process_hl7_event
            )
            
            logger.info("Starting message consumption...")
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            self.channel.stop_consuming()
            if self.connection:
                self.connection.close()
        except Exception as e:
            logger.error(f"Error in message consumption: {e}")

def main():
    """Main entry point"""
    logger.info("Starting ClinicHub Interoperability Worker")
    
    worker = ClinicHubInteropWorker()
    worker.start_consuming()

if __name__ == "__main__":
    main()