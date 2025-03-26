import asyncio
import os

from dotenv import load_dotenv
import uuid

load_dotenv()

from botcircuits import Options, BotCircuits, Request, Message


async def on_message(msg: Message):
    # This is an async callback; do anything you want here
    print("[Received Bot Message]")
    print("  type:", msg.type)
    print("  content:", msg.content)


async def main():
    options = Options(
        app_id=os.getenv('BOTCIRCUITS_APP_ID'),
        api_key=os.getenv('BOTCIRCUITS_API_KEY')
    )

    session_id = str(uuid.uuid4())

    bot = BotCircuits(options, session_id)

    # Start subscription with our async callback
    await bot.start_subscription(on_message)

    # Send a test message
    await bot.send_message(Request(textMessage="Hello"))

    try:
        # Keep running for 30s
        await asyncio.sleep(30)
    finally:
        # Gracefully close the bot connection
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
