import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
import sys
import json

sys.path.append("/workspace/backend")
from database import Base, get_db
from main import app
from models import User, ChateryWhatsAppSession

# Setup in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_webhook_lid_resolution():
    # Setup test data
    db = TestingSessionLocal()
    
    # 1. Create a user
    test_user = User(
        email="test@example.com",
        password_hash="fakehash",
        full_name="Test User"
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    # 2. Create a chatery session
    test_session = ChateryWhatsAppSession(
        session_id="2",
        user_id=test_user.id,
        status="connected"
    )
    db.add(test_session)
    db.commit()

    db.close()

    # Webhook payload from user's error report
    webhook_payload = {
        "event": "message", 
        "sessionId": "2", 
        "metadata": {"userId": 2}, 
        "data": {
            "id": "AC21A64649D679A637EC1EB2324A1515", 
            "chatId": "147527898800287@lid", 
            "fromMe": False, 
            "sender": "147527898800287@lid", 
            "senderPhone": "147527898800287", 
            "senderName": "nel", 
            "timestamp": 1776998435, 
            "type": "text", 
            "content": "hye", 
            "caption": None, 
            "mimetype": None, 
            "filename": None, 
            "mediaUrl": None, 
            "isGroup": False, 
            "quotedMessage": None
        }, 
        "timestamp": "2026-04-24T02:40:35.188Z"
    }

    # Use a mocked requests.post inside routes/chatery.py
    import routes.chatery as chatery
    import requests
    original_post = requests.post
    
    resolved_lid_called = False
    
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
        def json(self):
            return self.json_data
            
    def mock_post(url, *args, **kwargs):
        nonlocal resolved_lid_called
        if "contacts" in url:
            resolved_lid_called = True
            return MockResponse({
                "success": True,
                "contacts": [
                    {
                        "id": "147527898800287@lid",
                        "jid": "60123456789@s.whatsapp.net",
                        "name": "nel"
                    }
                ]
            }, 200)
        if "send-text" in url:
            return MockResponse({"success": True}, 200)
        return original_post(url, *args, **kwargs)
        
    requests.post = mock_post
    
    # Mock cs_agent
    import agents.cs_agent as cs_agent
    
    def mock_process_whatsapp_message(agent_payload):
        assert agent_payload["phone"] == "60123456789", f"Expected resolved phone, got {agent_payload['phone']}"
        return {"response": "Mock reply", "user_id": agent_payload["user_id"], "phone": agent_payload["phone"]}
        
    cs_agent.process_whatsapp_message = mock_process_whatsapp_message

    # Trigger webhook
    response = client.post("/api/chatery/webhook", json=webhook_payload)
    
    assert response.status_code == 200
    assert resolved_lid_called, "LID resolution API was not called!"
    print("Test passed! LID resolution was triggered successfully.")

if __name__ == "__main__":
    test_webhook_lid_resolution()