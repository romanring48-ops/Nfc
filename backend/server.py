from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import uuid
import json
import base64
from datetime import datetime

# Initialize FastAPI
app = FastAPI(title="NFC Contact Manager", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URL)
db = client.nfc_manager
contacts_collection = db.contacts

# Pydantic models
class Contact(BaseModel):
    id: Optional[str] = None
    phone_number: str = Field(..., min_length=1, max_length=20)
    text: str = Field(..., max_length=100)
    name: Optional[str] = Field(default="", max_length=50)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ContactResponse(BaseModel):
    id: str
    phone_number: str
    text: str
    name: str
    created_at: datetime
    updated_at: datetime
    ndef_data: str
    data_size: int

def generate_ndef_record(phone_number: str, text: str, name: str = "") -> dict:
    """Generate NDEF record for NFC 215 tag"""
    
    # Create vCard format for contact
    vcard_data = f"""BEGIN:VCARD
VERSION:3.0
FN:{name if name else phone_number}
TEL:{phone_number}
NOTE:{text}
END:VCARD""".strip()
    
    # Create NDEF record structure
    ndef_record = {
        "type": "text/vcard",
        "payload": vcard_data,
        "payload_base64": base64.b64encode(vcard_data.encode('utf-8')).decode('utf-8'),
        "size_bytes": len(vcard_data.encode('utf-8'))
    }
    
    return ndef_record

@app.get("/")
async def root():
    return {"message": "NFC Contact Manager API", "status": "running"}

@app.get("/api/contacts", response_model=List[ContactResponse])
async def get_contacts():
    """Get all contacts"""
    try:
        contacts = list(contacts_collection.find().sort("created_at", -1))
        result = []
        
        for contact in contacts:
            ndef_data = generate_ndef_record(
                contact["phone_number"], 
                contact["text"], 
                contact.get("name", "")
            )
            
            result.append({
                "id": contact["id"],
                "phone_number": contact["phone_number"],
                "text": contact["text"],
                "name": contact.get("name", ""),
                "created_at": contact["created_at"],
                "updated_at": contact["updated_at"],
                "ndef_data": ndef_data["payload_base64"],
                "data_size": ndef_data["size_bytes"]
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching contacts: {str(e)}")

@app.post("/api/contacts", response_model=ContactResponse)
async def create_contact(contact: Contact):
    """Create a new contact"""
    try:
        # Generate unique ID and timestamps
        contact_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Validate NFC 215 size limit (504 bytes)
        ndef_data = generate_ndef_record(contact.phone_number, contact.text, contact.name or "")
        if ndef_data["size_bytes"] > 504:
            raise HTTPException(
                status_code=400, 
                detail=f"Data too large for NFC 215 tag. Size: {ndef_data['size_bytes']} bytes (max: 504 bytes)"
            )
        
        contact_doc = {
            "id": contact_id,
            "phone_number": contact.phone_number,
            "text": contact.text,
            "name": contact.name or "",
            "created_at": now,
            "updated_at": now
        }
        
        contacts_collection.insert_one(contact_doc)
        
        return {
            "id": contact_id,
            "phone_number": contact.phone_number,
            "text": contact.text,
            "name": contact.name or "",
            "created_at": now,
            "updated_at": now,
            "ndef_data": ndef_data["payload_base64"],
            "data_size": ndef_data["size_bytes"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating contact: {str(e)}")

@app.put("/api/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: str, contact: Contact):
    """Update a contact"""
    try:
        existing_contact = contacts_collection.find_one({"id": contact_id})
        if not existing_contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        # Validate NFC 215 size limit
        ndef_data = generate_ndef_record(contact.phone_number, contact.text, contact.name or "")
        if ndef_data["size_bytes"] > 504:
            raise HTTPException(
                status_code=400, 
                detail=f"Data too large for NFC 215 tag. Size: {ndef_data['size_bytes']} bytes (max: 504 bytes)"
            )
        
        updated_doc = {
            "$set": {
                "phone_number": contact.phone_number,
                "text": contact.text,
                "name": contact.name or "",
                "updated_at": datetime.utcnow()
            }
        }
        
        contacts_collection.update_one({"id": contact_id}, updated_doc)
        
        updated_contact = contacts_collection.find_one({"id": contact_id})
        
        return {
            "id": contact_id,
            "phone_number": updated_contact["phone_number"],
            "text": updated_contact["text"],
            "name": updated_contact["name"],
            "created_at": updated_contact["created_at"],
            "updated_at": updated_contact["updated_at"],
            "ndef_data": ndef_data["payload_base64"],
            "data_size": ndef_data["size_bytes"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating contact: {str(e)}")

@app.delete("/api/contacts/{contact_id}")
async def delete_contact(contact_id: str):
    """Delete a contact"""
    try:
        result = contacts_collection.delete_one({"id": contact_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        return {"message": "Contact deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting contact: {str(e)}")

@app.get("/api/contacts/{contact_id}/ndef")
async def get_contact_ndef(contact_id: str):
    """Get NDEF data for a specific contact"""
    try:
        contact = contacts_collection.find_one({"id": contact_id})
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        ndef_data = generate_ndef_record(
            contact["phone_number"], 
            contact["text"], 
            contact.get("name", "")
        )
        
        return {
            "contact_id": contact_id,
            "ndef_record": ndef_data,
            "instructions": {
                "nfc_215_compatible": ndef_data["size_bytes"] <= 504,
                "recommended_apps": [
                    "NFC Tools (Android/iOS)",
                    "TagWriter by NXP (Android/iOS)",
                    "NFC TagInfo (Android)"
                ],
                "usage": "Copy the payload data and use an NFC writing app to write to your NFC 215 tag"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting NDEF data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)