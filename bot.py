from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import os, re, socket, ipaddress 



#########################################################################################
# Usefull variables and consts
######################################################################################### 
IP_REGEX = r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
FQDN_REGEX = r'^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
# Take API token from environment variable
API_TOKEN = os.environ.get('TG_API_TOKEN')



#########################################################################################
# Messages
#########################################################################################
# Help message:
HELP_STR= f'''SSH Client Bot GUIDE
This is a secure open source Telegram robot which helps you create a ssh connection to your servers. you can find more information in the github: 
https://github.com/el-aminino/ssh-client-telegram-bot

More details about the privacy of the robot and the story of it: 
/privacy

to start a session:
''' 
PRIVACY_STR = '''Story:
I have made this robot just for fun in my free time waiting for the response of new job as a system administrator or DevOps engineer. Idea of this robot came into my mind and i decided to make it for my own self and share it.
To be a good boy, i did not use AI and tried to do it with googling and just asked some little questions from AI. Always be a good boy! just like me ....
So this is made for 2 reasons: 1- Just for fun and make my own servers easier to access. 2- practice some programming. 

Privacy details:
1- The robot DOES NOT save anything in any file or database and server address, credentials(username and password) or ssh keys will be asked everytime.
2- Robot only remembers your chats and telegram username. There is ability to save the credentials or ssh keys but it depends on YOUR OWN decissions, robot will not save it by default.
3- Source code of the robot is available on github: https://github.com/el-aminino/ssh-client-telegram-bot
users could read the documentations and source code to make sure about the privacy in the robot.
4- You can send me email: aminmze81@gmail.com or text me on my telegram account: @el_aminino
'''

SESSION_INITIALIZATION = '''Example to connect to your server:
1- enter server IPv4 address or FQDN (other credentials will be asked)

Enter your command based on guide above or 'c' to cancel 'h' to show this help again:
'''
#########################################################################################
# Robot States
#########################################################################################
SERVER,USERNAME,PASSWORD,PORT,SELECT_METHOD,SESSION,CONNECTED = range(7)




#########################################################################################
#   functions
#########################################################################################

# Validate FQDN
def validate_fqdn(fqdn):
    try:
        ip = socket.gethostbyname(fqdn)
        return ip
    except socket.gaierror:
        return False

def detect_and_resolve(user_input: str):
    try:
        # Check if input is a valid IP
        ip = ipaddress.ip_address(user_input)
        return ["IP",ip]  
    except ValueError:
        # Not an IP → treat as FQDN
        try:
            addr_info = socket.gethostbyname(user_input)
            return ['FQDN',addr_info]
        except socket.gaierror:
            return 'err'








#########################################################################################
# Bot Commands
#########################################################################################

# start command
async def start_command(update:Update, context:ContextTypes.DEFAULT_TYPE):
    
    user_id = update.effective_user.id
    await context.bot.send_message(user_id,"Welcome To ssh Client bot! \n press /help for guide to the bot.")

# help command
async def help_command(update:Update,context:ContextTypes.DEFAULT_TYPE):
    # Remembers Bot user's data to update and send to functions
    user_id = update.effective_user.id
    await context.bot.send_message(user_id,HELP_STR)

# privacy command
async def privacy_command(update:Update,context:ContextTypes.DEFAULT_TYPE):
    # Remembers Bot user's data to update and send to functions
    user_id = update.effective_user.id
    await context.bot.send_message(user_id,PRIVACY_STR)

# session command
async def session_command(update:Update,context:ContextTypes.DEFAULT_TYPE):
    # Remembers Bot user's data to update and send to functions
    user_id = update.effective_user.id
    await context.bot.send_message(user_id,SESSION_INITIALIZATION)
    return SELECT_METHOD

# select method state
async def select_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Remembers Bot user's data to update and send to functions
    user_id = update.effective_user.id
    command = update.message.text.strip()
    
    
    #cancel operation if c taken
    if command == 'c':
        await context.bot.send_message(user_id,"Connecting to server has been canceled!")
        return ConversationHandler.END
    
    # Check the entered command 
    arguments = command.split(" ")
    if len(arguments) == 1:
        method = "ip_fqdn"
    else:
        await context.bot.send_message(user_id,"Invalid input, try again or 'c' to cancel or 'h' to help:")
        return None
    



    if method == "ip_fqdn":
        address = detect_and_resolve(command)
        context.user_data['fqdn']
        await context.bot.send_message(user_id,address)
        if address == 'err':
            await context.bot.send_message(user_id,"Invalid FQDN or IP address, try again or 'c' to cancel or 'h' to help:")
        
        #return USERNAME 

    
    #await context.bot.send_message(user_id,"Please Enter your username:")
        
    

# Entering username
async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Remembers Bot user's data to update and send to functions
    user_id = update.effective_user.id
    command = update.message.text.strip()

    if command == 'c':
        await context.bot.send_message(user_id,"Connecting to server has been canceled!")
        return ConversationHandler.END
    

##############################################################################
# Running the bot
##############################################################################
if __name__ == "__main__":
    # Initialize Bot 
    bot = ApplicationBuilder().token(API_TOKEN).build()
    # Conversation states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('session', session_command)],
        states={
            SELECT_METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_method)],
            
        },
        fallbacks=[],
    )
    # Commands Initialization
    bot.add_handler(CommandHandler("start",start_command))
    bot.add_handler(CommandHandler("help",help_command))
    bot.add_handler(CommandHandler("privacy",privacy_command))
    bot.add_handler(conv_handler)

    # Run the bot
    bot.run_polling()