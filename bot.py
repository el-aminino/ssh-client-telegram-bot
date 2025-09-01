from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import os


# Take API token from environment variable
API_TOKEN = os.environ.get('TG_API_TOKEN')


# Robot States
USERNAME,PASSWORD,SERVER,PORT,SESSION = range(5)


async def start_command(update:Update, context:ContextTypes.DEFAULT_TYPE):
    # Remembers Bot user's data to update and send to functions
    user_id = update.effective_user.id
    
    await context.bot.send_message(user_id,"Welcome To ssh Client bot! \n press /help for guide to the bot.")
 
if __name__ == "__main__":
    # Initialize Bot 
    bot = ApplicationBuilder().token(API_TOKEN).build()
    
    bot.add_handler(CommandHandler("start",start_command))