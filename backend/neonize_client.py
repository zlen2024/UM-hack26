import os
import threading
import time
import base64
from typing import Dict, Any, Optional
import io
import qrcode
from sqlalchemy.orm import Session
from database import SessionLocal

from neonize.client import NewClient
from neonize.events import ConnectedEv, MessageEv, PairStatusEv, QREv

from agents.cs_agent import process_whatsapp_message
from models import NeonizeConfig

# Ensure data directory exists
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

class NeonizeManager:
    def __init__(self):
        self.clients: Dict[int, NewClient] = {}
        self.client_threads: Dict[int, threading.Thread] = {}
        self.qr_codes: Dict[int, str] = {}
        self.lock = threading.Lock()

    def get_session_path(self, user_id: int) -> str:
        return os.path.join(DATA_DIR, f"whatsapp_session_{user_id}.sqlite3")

    def start_client(self, user_id: int) -> bool:
        with self.lock:
            if user_id in self.clients:
                return True  # Already started

            session_file = self.get_session_path(user_id)
            client = NewClient(session_file)

            # Define event handlers
            @client.event(QREv)
            def on_qr_code(client: NewClient, event: QREv):
                print(f"[Neonize] user_id {user_id}: QR Code generated")
                qr_data = "".join(event.Codes) if hasattr(event, "Codes") and event.Codes else ""
                # Generate base64 PNG from QR string
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(qr_data)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                with self.lock:
                    self.qr_codes[user_id] = f"data:image/png;base64,{img_str}"
                    
            @client.event(PairStatusEv)
            def on_pair_status(client: NewClient, event: PairStatusEv):
                print(f"[Neonize] user_id {user_id}: Pair status: {event}")

            @client.event(ConnectedEv)
            def on_connected(client: NewClient, event: ConnectedEv):
                print(f"[Neonize] user_id {user_id}: Connected successfully!")
                with self.lock:
                    if user_id in self.qr_codes:
                        del self.qr_codes[user_id]
                
                # Update DB state
                try:
                    db = SessionLocal()
                    config = db.query(NeonizeConfig).filter(NeonizeConfig.user_id == user_id).first()
                    if config:
                        config.is_connected = True
                        db.commit()
                    db.close()
                except Exception as e:
                    print(f"Error updating DB on connect: {e}")

            @client.event(MessageEv)
            def on_message(client: NewClient, event: MessageEv):
                msg_content = event.Message.conversation or (event.Message.extendedTextMessage.text if event.Message.extendedTextMessage else "")
                
                if not msg_content:
                    return

                sender_jid = event.Info.MessageSource.Sender.User
                chat_jid = event.Info.MessageSource.Chat
                sender_name = event.Info.Pushname or ""

                # Ignore own messages or status broadcasts
                if event.Info.MessageSource.IsFromMe or "@broadcast" in chat_jid:
                    return

                print(f"[Neonize] user_id {user_id} received message from {sender_jid}: {msg_content}")

                # Process message via AI Agent in a separate thread so we don't block neonize
                def process_and_reply():
                    try:
                        message_data = {
                            "user_id": user_id,
                            "contact_name": sender_name,
                            "phone": sender_jid,
                            "message": msg_content
                        }
                        result = process_whatsapp_message(message_data)
                        response_text = result.get("response", "")
                        if response_text:
                            client.send_message(chat_jid, response_text)
                    except Exception as e:
                        print(f"[Neonize] Error processing message: {e}")

                threading.Thread(target=process_and_reply, daemon=True).start()

            self.clients[user_id] = client

            # Start client in a background thread
            def run():
                try:
                    client.connect()
                except Exception as e:
                    print(f"[Neonize] Client error for user_id {user_id}: {e}")
                finally:
                    # Clean up if disconnected
                    with self.lock:
                        if user_id in self.clients:
                            del self.clients[user_id]

            thread = threading.Thread(target=run, daemon=True)
            self.client_threads[user_id] = thread
            thread.start()
            
            return True

    def get_status(self, user_id: int) -> Dict[str, Any]:
        with self.lock:
            client = self.clients.get(user_id)
            qr_code = self.qr_codes.get(user_id)
            
            # Use neonize API to check if connected if possible
            is_connected = False
            if client:
                try:
                    is_connected = client.is_connected()
                except:
                    # Fallback check
                    pass

        try:
            db = SessionLocal()
            config = db.query(NeonizeConfig).filter(NeonizeConfig.user_id == user_id).first()
            if config:
                is_connected = is_connected or config.is_connected
            db.close()
        except:
            pass

        return {
            "started": client is not None,
            "connected": is_connected,
            "has_qr": qr_code is not None,
            "qr_code": qr_code
        }

    def stop_client(self, user_id: int):
        with self.lock:
            client = self.clients.get(user_id)
            if client:
                try:
                    client.disconnect()
                except:
                    pass
                del self.clients[user_id]
                
            if user_id in self.qr_codes:
                del self.qr_codes[user_id]

    def disconnect_session(self, user_id: int):
        self.stop_client(user_id)
        
        # Remove session file
        session_file = self.get_session_path(user_id)
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
            except Exception as e:
                print(f"Failed to remove session file: {e}")
                
        # Update DB
        try:
            db = SessionLocal()
            config = db.query(NeonizeConfig).filter(NeonizeConfig.user_id == user_id).first()
            if config:
                config.is_connected = False
                db.commit()
            db.close()
        except Exception as e:
            print(f"Error updating DB on disconnect: {e}")

    def send_message(self, user_id: int, phone: str, text: str) -> bool:
        client = self.clients.get(user_id)
        if not client:
            return False
            
        try:
            jid = client.build_jid(phone)
            client.send_message(jid, text)
            return True
        except Exception as e:
            print(f"[Neonize] Send message error: {e}")
            return False

# Global instance
manager = NeonizeManager()
