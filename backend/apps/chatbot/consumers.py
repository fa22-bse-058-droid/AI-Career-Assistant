"""
WebSocket consumer for AI Chatbot using Django Channels.
"""
import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are CareerBot, an AI career assistant. Help users with job searching, "
    "CV writing, interview preparation, and career advice. Be concise and helpful."
)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.user = user
        self.conversation_id = self.scope["url_route"]["kwargs"].get("conversation_id")
        await self.accept()
        logger.info("WebSocket connected for user %s", user.email)

    async def disconnect(self, close_code):
        logger.info("WebSocket disconnected: %s", close_code)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            user_message = data.get("message", "").strip()
            if not user_message:
                return

            # Save user message
            conversation = await self.get_or_create_conversation()
            await self.save_message(conversation, "user", user_message)

            # Get conversation history (last 5 turns)
            history = await self.get_history(conversation)

            # Generate bot response
            bot_response = await self.generate_response(user_message, history)

            # Save bot message
            await self.save_message(conversation, "bot", bot_response)

            await self.send(text_data=json.dumps({
                "type": "bot_message",
                "message": bot_response,
                "conversation_id": str(conversation.id),
            }))

        except Exception as e:
            logger.error("ChatConsumer error: %s", e)
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "An error occurred. Please try again.",
            }))

    @database_sync_to_async
    def get_or_create_conversation(self):
        from .models import Conversation
        if self.conversation_id:
            try:
                return Conversation.objects.get(id=self.conversation_id, user=self.user)
            except Conversation.DoesNotExist:
                pass
        return Conversation.objects.create(
            user=self.user,
            title=f"Chat {timezone.now().strftime('%Y-%m-%d %H:%M')}",
        )

    @database_sync_to_async
    def save_message(self, conversation, role, content):
        from .models import ChatMessage
        return ChatMessage.objects.create(
            conversation=conversation,
            role=role,
            content=content,
        )

    @database_sync_to_async
    def get_history(self, conversation):
        from .models import ChatMessage
        messages = ChatMessage.objects.filter(conversation=conversation).order_by(
            "-timestamp"
        )[:10]
        return list(reversed([(m.role, m.content) for m in messages]))

    async def generate_response(self, user_message: str, history: list) -> str:
        """Generate AI response using BlenderBot or DialoGPT."""
        try:
            from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration
            import torch

            model_name = "facebook/blenderbot-400M-distill"

            # Build context from history
            context = ""
            for role, content in history[-5:]:
                context += f"{'Person' if role == 'user' else 'Bot'}: {content}\n"

            full_input = f"{SYSTEM_PROMPT}\n\n{context}Person: {user_message}\nBot:"

            # Use cached model if available
            tokenizer = BlenderbotTokenizer.from_pretrained(model_name)
            model = BlenderbotForConditionalGeneration.from_pretrained(model_name)

            inputs = tokenizer(
                [full_input[:512]],
                return_tensors="pt",
                truncation=True,
                max_length=512,
            )
            with torch.no_grad():
                reply_ids = model.generate(**inputs, max_new_tokens=200)
            response = tokenizer.decode(reply_ids[0], skip_special_tokens=True)
            return response.strip()
        except Exception as e:
            logger.error("AI generation failed: %s", e)
            return (
                "I'm here to help with your career! You can ask me about CV writing, "
                "job searching, or interview tips."
            )
