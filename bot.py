import subprocess
import sys
import os
import venv
import pip

# List of required libraries
required_libraries = ['openai', 'python-telegram-bot']

# Check for and install missing libraries in a virtual environment
def install_libraries():
    # Path to virtual environment
    venv_path = 'venv'
    
    # Create the virtual environment if it does not exist
    if not os.path.exists(venv_path):
        print("Creating virtual environment...")
        venv.create(venv_path, with_pip=True)

    # Activate the virtual environment
    activate_script = os.path.join(venv_path, 'bin', 'activate_this.py')
    exec(open(activate_script).read(), {'__file__': activate_script})

    # Install required libraries
    for library in required_libraries:
        try:
            __import__(library)
            print(f"{library} is already installed.")
        except ImportError:
            print(f"{library} not found. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", library])

    print("All required libraries are installed.")

# Run the installation process
install_libraries()

# Now, you can import your libraries and continue with your bot
import openai
import base64
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes
from telegram.ext.filters import PHOTO, TEXT

# Set up API keys (keep these safe, consider using environment variables)
OPENAI_API_KEY = "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"
TELEGRAM_API_KEY = "7289833807:AAFOqKJCMDlr2aIdiGVv-L6AYmlLRsQEprQ"
MODEL_NAME = "gpt-4o"
ENDPOINT = "https://models.inference.ai.azure.com"

# Configure OpenAI
openai.api_key = OPENAI_API_KEY
openai.api_base = ENDPOINT

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the user starts the bot."""
    await update.message.reply_text(
        "Hello! 👋 I'm your AI assistant. Here's what I can do:\n\n"
        "🤖 Chat with me by typing messages.\n"
        "🖼️ Send me an image, and I'll describe it for you.\n\n"
        "How can I help you today?"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages for chat."""
    user_message = update.message.text

    # Send a "thinking" message
    thinking_message = await update.message.reply_text("...")

    try:
        # Query the OpenAI API for a response
        response = openai.ChatCompletion.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": "You are a helpful and friendly assistant."},
                      {"role": "user", "content": user_message}],
        )
        reply = response['choices'][0]['message']['content']
        # Edit the "thinking" message with the actual reply
        await thinking_message.edit_text(reply)
    except Exception as e:
        # Edit the "thinking" message with an error message
        await thinking_message.edit_text(f"Sorry, I couldn't process your message. Error: {e}")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle image messages."""
    if not update.message.photo:
        await update.message.reply_text("Please send an image.")
        return

    # Send a "thinking" message
    thinking_message = await update.message.reply_text("Analyzing the image...")

    # Get the highest-resolution photo
    photo = update.message.photo[-1]
    file_id = photo.file_id

    # Download the image from Telegram
    bot = context.bot
    file = await bot.get_file(file_id)
    file_path = "received_image.jpg"
    await file.download_to_drive(file_path)

    # Convert the image to a data URL
    try:
        image_url = get_image_data_url(file_path, "jpeg")

        # Query the OpenAI API
        response = openai.ChatCompletion.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": "You are a helpful assistant that describes images in detail."},
                      {"role": "user", "content": [
                          {"type": "text", "text": "What's in this image?"},
                          {"type": "image_url", "image_url": {"url": image_url, "details": "low"}}
                      ]}]
        )
        description = response['choices'][0]['message']['content']
        # Edit the "thinking" message with the actual description
        await thinking_message.edit_text(description)
    except Exception as e:
        # Edit the "thinking" message with an error message
        await thinking_message.edit_text(f"An error occurred while processing the image: {e}")

def get_image_data_url(image_file: str, image_format: str) -> str:
    """
    Convert an image to a Base64 data URL.
    :param image_file: Path to the image file.
    :param image_format: Format of the image file, e.g., "jpeg".
    :return: Data URL of the image.
    """
    try:
        with open(image_file, "rb") as img:
            image_base64 = base64.b64encode(img.read()).decode("utf-8")
            return f"data:image/{image_format};base64,{image_base64}"
    except FileNotFoundError:
        raise ValueError(f"Could not read '{image_file}'.")

def main():
    """Start the bot."""
    application = ApplicationBuilder().token(TELEGRAM_API_KEY).build()

    # Command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(TEXT, handle_text))  # Handle chat messages
    application.add_handler(MessageHandler(PHOTO, handle_image))  # Handle image messages

    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
