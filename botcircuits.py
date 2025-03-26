import os
import json
import asyncio
import base64
import aiohttp
from pydantic import BaseModel
from typing import Optional, Callable, Coroutine

HOST = os.getenv("BOTCIRCUITS_HOST")
GRAPHQL_HTTP_API = f"https://{HOST}/graphql"
WEBSOCKET_API = f"wss://{HOST}/graphql/realtime"


class Options(BaseModel):
    apiKey: str
    appId: str


class Request(BaseModel):
    textMessage: Optional[str] = None
    voiceMessage: Optional[str] = None


class BotCircuits:
    def __init__(self, options: Options, session_id: str):
        self.options = options
        self.session_id = session_id

        # We'll store our subscription task so we can cancel it later
        self._subscription_task: Optional[asyncio.Task] = None
        self._on_message_callback: Optional[Callable[[str], None]] = None

    async def start_subscription(self, on_message: Callable[[str], None]):
        """
        Method to begin listening to subscription messages.
        Internally spawns a background task that calls `_subscribe`.
        `on_message` is a callback that receives the string message.
        """
        if self._subscription_task is not None:
            # Already started
            return

        self._on_message_callback = on_message
        self._subscription_task = asyncio.create_task(self._subscribe())

    async def _subscribe(self):
        """
        An internal async function that handles the actual WebSocket subscription,
        and calls the user-provided callback whenever new messages arrive.
        """
        import websockets  # install: pip install websockets

        # Prepare headers for connection
        header_dict = {
            "Authorization": self.options.apiKey,
            "host": HOST
        }
        headers_bytes = base64.b64encode(json.dumps(header_dict).encode("utf-8")).decode("utf-8")

        endpoint = f"{WEBSOCKET_API}?header={headers_bytes}&payload=e30="

        async with websockets.connect(endpoint, subprotocols=["graphql-ws"]) as websocket:

            print("[Connected]")
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
                            "appId": self.options.appId,
                            "sessionId": self.session_id
                        }
                    }),
                    "extensions": {
                        "authorization": {
                            "Authorization": self.options.apiKey,
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
                                text = original_message.get("message")
                                if text and self._on_message_callback:
                                    await self._on_message_callback(text)

                    elif msg_type == "connection_error":
                        errors = message.get("payload", {}).get("errors", [])
                        # You could handle or raise them; here we just log or print
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
            "appId": self.options.appId,
            "sessionId": self.session_id,
            "inputText": request.textMessage,
            "voiceMessage": request.voiceMessage,
        })

        variables = {
            "appId": self.options.appId,
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
                headers={"Authorization": self.options.apiKey},
                json=payload,
                timeout=10
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"HTTP {resp.status} - {text}")

    async def close(self):
        """Convenient close method that calls stop_subscription."""
        print("[Connection Closed]")
        await self.stop_subscription()
