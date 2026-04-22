import os
import asyncio
import base64
from typing import Dict, Any, Optional
import io
import qrcode
from sqlalchemy.orm import Session
from database import SessionLocal

from neonize.aioze.client import ClientFactory, NewAClient
from neonize.aioze.events import ConnectedEv, MessageEv, PairStatusEv, QREv

from agents.cs_agent import process_whatsapp_message
from models import NeonizeConfig

# Ensure data directory exists
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

class NeonizeManager:
    def __init__(self):
        self.session_file = os.path.join(DATA_DIR, "sessions.db")
        self.client_factory = ClientFactory(self.session_file)
        self.qr_codes: Dict[int, str] = {}

        self.setup_factory_events()

    def get_user_id_from_client(self, client: NewAClient) -> Optional[int]:
        try:
            # Client name format is "user_{user_id}"
            if hasattr(client, 'name') and client.name.startswith("user_"):
                return int(client.name.split("_")[1])
        except Exception:
            pass
        return None

    def setup_factory_events(self):
        @self.client_factory.event(ConnectedEv)
        async def on_connected(client: NewAClient, event: ConnectedEv):
            user_id = self.get_user_id_from_client(client)
            if user_id:
                print(f"[Neonize] user_id {user_id}: Connected successfully!")
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

        @self.client_factory.event(MessageEv)
        async def on_message(client: NewAClient, event: MessageEv):
            user_id = self.get_user_id_from_client(client)
            if not user_id:
                return

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

            # Process message via AI Agent non-blocking
            try:
                message_data = {
                    "user_id": user_id,
                    "contact_name": sender_name,
                    "phone": sender_jid,
                    "message": msg_content
                }

                # Use to_thread since process_whatsapp_message might be blocking
                result = await asyncio.to_thread(process_whatsapp_message, message_data)
                response_text = result.get("response", "")

                if response_text:
                    await client.reply_message(response_text, event)
            except Exception as e:
                print(f"[Neonize] Error processing message: {e}")

    async def start_all_clients(self):
        """Start all previously connected sessions on startup"""
        print("[Neonize] Loading existing sessions...")
        try:
            for device in self.client_factory.get_all_devices():
                self.client_factory.new_client(device.JID)
                print(f"[Neonize] Loaded device JID: {device.JID}")

            # Connect all clients in background
            asyncio.create_task(self.client_factory.run())
        except Exception as e:
            print(f"[Neonize] Error starting clients: {e}")

    async def start_client(self, user_id: int) -> bool:
        device_name = f"user_{user_id}"

        # Check if already in factory
        for c in self.client_factory.clients:
            if getattr(c, 'name', '') == device_name or getattr(c, 'device_name', '') == device_name:
                return True

        client = self.client_factory.new_client(uuid=device_name)

        # We need to manually set a name property to identify it later in factory events
        client.name = device_name

        @client.qr
        async def on_qr_code(c: NewAClient, qr_data_bytes: bytes):
            print(f"[Neonize] user_id {user_id}: QR Code generated")
            qr_data = qr_data_bytes.decode() if isinstance(qr_data_bytes, bytes) else str(qr_data_bytes)
            # Generate base64 PNG from QR string
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

            self.qr_codes[user_id] = f"data:image/png;base64,{img_str}"

        # Connect this specific client
        asyncio.create_task(client.connect())
        return True

    async def get_status(self, user_id: int) -> Dict[str, Any]:
        device_name = f"user_{user_id}"

        client = None
        for c in self.client_factory.clients:
            if getattr(c, 'name', '') == device_name or getattr(c, 'device_name', '') == device_name:
                client = c
                break

        qr_code = self.qr_codes.get(user_id)

        is_connected = False
        if client:
            try:
                is_connected = await client.is_connected
            except:
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

    async def stop_client(self, user_id: int):
        device_name = f"user_{user_id}"
        
        client = None
        for c in self.client_factory.clients:
            if getattr(c, 'name', '') == device_name or getattr(c, 'device_name', '') == device_name:
                client = c
                break

        if client:
            try:
                await client.disconnect()
            except:
                pass
            if client in self.client_factory.clients:
                self.client_factory.clients.remove(client)
                
        if user_id in self.qr_codes:
            del self.qr_codes[user_id]

    async def disconnect_session(self, user_id: int):
        await self.stop_client(user_id)

        # We cannot easily remove a specific session from sessions.db using the factory
        # For now, we update DB status
        try:
            db = SessionLocal()
            config = db.query(NeonizeConfig).filter(NeonizeConfig.user_id == user_id).first()
            if config:
                config.is_connected = False
                db.commit()
            db.close()
        except Exception as e:
            print(f"Error updating DB on disconnect: {e}")

    async def send_message(self, user_id: int, phone: str, text: str) -> bool:
        device_name = f"user_{user_id}"
        client = None
        for c in self.client_factory.clients:
            if getattr(c, 'name', '') == device_name or getattr(c, 'device_name', '') == device_name:
                client = c
                break

        if not client:
            return False
            
        try:
            jid = client.build_jid(phone)
            await client.send_message(jid, text)
            return True
        except Exception as e:
            print(f"[Neonize] Send message error: {e}")
            return False

# Global instance
manager = NeonizeManager()
