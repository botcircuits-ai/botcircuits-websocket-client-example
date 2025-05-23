import os
import json
import asyncio
import base64
import aiohttp
from pydantic import BaseModel
from typing import Optional, Callable, Coroutine, Any, Dict

HOST = os.getenv("BOTCIRCUITS_HOST")
GRAPHQL_HTTP_API = f"https://{HOST}/graphql"
WEBSOCKET_API = f"wss://{HOST}/graphql/realtime"


class Options(BaseModel):
    app_id: str
    api_key: str


class Request(BaseModel):
    textMessage: Optional[str] = None
    requestAttributes: Optional[Dict[str, Any]] = None


class Message(BaseModel):
    """Represents the bot message structure."""
    type: str
    content: Any


class BotCircuits:
    def __init__(self, options: Options, session_id: str):
        self.options = options
        self.session_id = session_id

        # We'll store our subscription task so we can cancel it later
        self._subscription_task: Optional[asyncio.Task] = None
        # The callback now expects a `Message` object
        self._on_message_callback: Optional[Callable[[Message], Coroutine[Any, Any, None]]] = None

    async def start_subscription(self, on_message: Callable[[Message], Coroutine[Any, Any, None]]):
        """
        Method to begin listening to subscription messages.
        Internally spawns a background task that calls `_subscribe`.
        `on_message` is an async callback that receives a `Message` object.
        """
        if self._subscription_task is not None:
            # Already started
            return

        self._on_message_callback = on_message
        self._subscription_task = asyncio.create_task(self._subscribe())

    async def _subscribe(self):
        import websockets  # pip install websockets

        # Prepare headers for connection
        header_dict = {
            "Authorization": self.options.api_key,
            "host": HOST
        }
        headers_bytes = base64.b64encode(json.dumps(header_dict).encode("utf-8")).decode("utf-8")

        endpoint = f"{WEBSOCKET_API}?header={headers_bytes}&payload=e30="

        async with websockets.connect(endpoint, subprotocols=["graphql-ws"]) as websocket:
            # connection_init
            await websocket.send(json.dumps({"type": "connection_init"}))

            # Send GraphQL subscription
            query = """
            subscription Subscribe($appId: String!, $sessionId: String!) {
              subscribeBotMessage(appId: $appId, sessionId: $sessionId) {
                data
                appId
                sessionId
              }
            }
            """
            payload = {
                "id": self.session_id,
                "payload": {
                    "data": json.dumps({
                        "query": query,
                        "variables": {
                            "appId": self.options.app_id,
                            "sessionId": self.session_id
                        }
                    }),
                    "extensions": {
                        "authorization": {
                            "Authorization": self.options.api_key,
                            "host": HOST,
                            "x-amz-user-agent": "aws-amplify/4.7.14 js"
                        }
                    },
                },
                "type": "start"
            }
            await websocket.send(json.dumps(payload))

            # Listen for messages
            try:
                while True:
                    message_str = await websocket.recv()
                    message = json.loads(message_str)
                    msg_type = message.get("type")

                    if msg_type == "data":
                        payload = message.get("payload", {})
                        data_obj = payload.get("data", {})
                        subscribe_data = data_obj.get("subscribeBotMessage")
                        if subscribe_data:
                            original_data_str = subscribe_data.get("data")
                            if original_data_str:
                                original_message = json.loads(original_data_str)
                                # Expecting structure: {"message": {"type": "...", "content": ...}}
                                bot_msg_dict = original_message.get("message", {})
                                if bot_msg_dict and self._on_message_callback:
                                    try:
                                        # Parse into a Message object
                                        msg_obj = Message(**bot_msg_dict)
                                        await self._on_message_callback(msg_obj)
                                    except Exception as e:
                                        print("[Parse Error]", e)

                    elif msg_type == "connection_error":
                        errors = message.get("payload", {}).get("errors", [])
                        print("[Subscription Error]", errors)

            except asyncio.CancelledError:
                # Graceful exit if subscription is stopped
                pass

    async def stop_subscription(self):
        """
        Public method to stop listening and cancel the subscription task.
        """
        if self._subscription_task:
            self._subscription_task.cancel()
            try:
                await self._subscription_task
            except asyncio.CancelledError:
                pass
            self._subscription_task = None

    async def send_message(self, request: Request):
        """
        Send a message using GraphQL over HTTPS (async).
        """
        mutation = """
        mutation Publish($data: AWSJSON!, $appId: String!, $sessionId: String!) {
          sendUserMessage(data: $data, appId: $appId, sessionId: $sessionId) {
            data
            appId
            sessionId
          }
        }
        """
        request_data = json.dumps({
            "action": "executor",
            "appId": self.options.app_id,
            "sessionId": self.session_id,
            "inputText": request.textMessage,
            "requestAttributes": request.requestAttributes
        })

        variables = {
            "appId": self.options.app_id,
            "sessionId": self.session_id,
            "data": request_data,
        }
        payload = {
            "query": mutation,
            "variables": variables,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                GRAPHQL_HTTP_API,
                headers={"Authorization": self.options.api_key},
                json=payload,
                timeout=10
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"HTTP {resp.status} - {text}")
                else:
                    print("[Thinking...]")

    async def close(self):
        """Convenient close method that calls stop_subscription."""
        print("[Connection Closed]")
        await self.stop_subscription()
