from dotenv import load_dotenv
load_dotenv()

import asyncio
import os

from botcircuits import Options, BotCircuits, Request


async def main():
    # Construct the options
    options = Options(
        appId=os.getenv('BOTCIRCUITS_APP_ID'),  # your appId
        apiKey = os.getenv('BOTCIRCUITS_API_KEY'),  # your JWT
    )

    # Create the AsyncBotCircuits object
    bot = BotCircuits(options, session_id="my-async-session-123")

    # Define a simple callback to handle incoming messages
    def on_message(msg: str):
        print("[Received Bot Message]:", msg)

    # Start subscription with your callback
    await bot.start_subscription(on_message)

    # Optionally send a message
    await bot.send_message(Request(textMessage="Hello"))

    # Let the subscription run for a bit
    try:
        await asyncio.sleep(30)
    finally:
        # Stop subscription and close
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
