# BotCircuits Python Client Example

This repository provides a Python-based client for interacting with the BotCircuits WebSocket APIs. It demonstrates how to:

1. Send and Receive messages in real-time via a WebSocket subscription.
2. Callback to handle incoming messages

---

## Prerequisites

- Python 3.9+
- An environment with your BotCircuits credentials (e.g., `BOTCIRCUITS_API_KEY`, `BOTCIRCUITS_APP_ID`) stored in a `.env` file.

---

## Setup

Below is a quick guide to set this project up and run it using a Python virtual environment.

1. Clone this repository (or download the code).

2. Create a virtual environment:
   ```bash
   python -m venv venv

3. Activate the virtual environment:
* On Mac/Linux:
```
source venv/bin/activate
```

* On Windows:
```
venv\Scripts\activate
```

4. Install dependencies:
```shell
pip install -r requirements.txt
```
5. Create a .env file (if not already present) containing:
````
BOTCIRCUITS_HOST=your-host.example.com
BOTCIRCUITS_API_KEY=your-api-key
BOTCIRCUITS_APP_ID=your-app-id
````


## Running the Example
From your terminal within the virtual environment:

```shell
python app.py
```

## High-Level Explanation
BotCircuits Class (botcircuits.py)
1. Initialization
```shell
bot = BotCircuits(options, session_id="some-session-id")
```
* Takes Options (API key, App ID) and a session_id.
* Sets up internal fields for later use.

2. Starting the Subscription
```
await bot.start_subscription(on_message_callback)
```
* Spawns a background async task (_subscribe) that connects to the WebSocket endpoint.
* Sends a GraphQL subscription message.
* Listens for real-time messages.
* Whenever a new message arrives, it parses the payload into a Message object and invokes your callback.

3. Sending Messages
```
await bot.send_message(Request(textMessage="Hello!"))
```
* Issues a GraphQL mutation over HTTPS, sending your Request object (text).
* The server processes it and will eventually push back a response via the subscription.

4. Closing
await bot.close()

## app.py Usage
1. Load environment variables from .env using python-dotenv.
2. Create the BotCircuits instance with your credentials.
3. Define an async callback on_message(msg: Message) to handle incoming data.
4. Start the subscription to receive real-time bot messages.
5. Send a test message.
6. Sleep or keep the loop running to allow messages to be received.
7. Close (stop subscription) gracefully.
