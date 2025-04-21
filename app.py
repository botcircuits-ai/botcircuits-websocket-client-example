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

    print("Type a message to send to the bot. Type '/q' to quit.")

    # Continuously read user input and send to the bot
    while True:
        user_input = await asyncio.to_thread(input)

        # Check for exit condition
        if user_input.strip().lower() == "/q":
            print("[Exiting]")
            break

        if user_input.strip():
            # for the whatsapp channels, set user's phone_number into requestAttributes
            test_phone_no = "94713132456"
            await bot.send_message(Request(textMessage=user_input, requestAttributes={"phone_number": test_phone_no}))

    await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
