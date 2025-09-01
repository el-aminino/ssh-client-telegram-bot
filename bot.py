from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import os, re, socket, ipaddress 
import paramiko
import threading
import time
import html

#########################################################################################
# Usefull variables and consts
######################################################################################### 
IP_REGEX = r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
FQDN_REGEX = r'^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
# Take API token from environment variable
API_TOKEN = os.environ.get('TG_API_TOKEN')

ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


sessions = {}

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
# Privacy message
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
SERVER,USERNAME,PASSWORD,SELECT_METHOD,SESSION,CONNECTED,CONFIRM_SSH = range(7)




#########################################################################################
#   functions
#########################################################################################

# Validate FQDN
def validate_fqdn(fqdn):
    try:
        ip = socket.gethostbyname(fqdn)
        return str(ip)
    except socket.gaierror:
        return False

# Validating and exporting FQDN and IP
def detect_and_resolve(user_input: str):
    try:
        # Check if input is a valid IP
        ip = ipaddress.ip_address(user_input)
        return ["IP",str(ip)]  
    except ValueError:
        # Not an IP → treat as FQDN
        try:
            addr_info = socket.gethostbyname(user_input)
            return ['FQDN',addr_info]
        except socket.gaierror:
            return 'err'



def clean_output(text: str) -> str:
    # Strip ANSI escape codes
    text = ansi_escape.sub('', text)
    # Escape HTML special characters
    return html.escape(text).strip()

# SSH Connection
def start_ssh_session(chat_id, ssh_info):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ssh_info["ssh_host"], username=ssh_info["ssh_user"], password=ssh_info["ssh_pass"])
    channel = client.invoke_shell()
    channel.settimeout(0.5)

    buffer = {"data": ""}   # mutable container

    def reader():
        while True:
            try:
                if channel.recv_ready():
                    data = channel.recv(4096).decode(errors="ignore")
                    buffer["data"] += data
            except Exception:
                pass
            time.sleep(0.1)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()

    return {"client": client, "channel": channel, "buffer": buffer, "thread": thread}








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
        if address == 'err':
            await context.bot.send_message(user_id,"Invalid FQDN or IP address, try again or 'c' to cancel or 'h' to help:")
            return None
        if address[0] == 'IP':
            context.user_data['IP'] = address[1]
        if address[0] == 'FQDN':
            context.user_data['FQDN'] = command
            context.user_data['IP'] = address[1]
        await context.bot.send_message(user_id,"Please enter user name:")
        return USERNAME         
    

# Entering username
async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Remembers Bot user's data to update and send to functions
    user_id = update.effective_user.id
    command = update.message.text.strip()

    if command == 'c':
        await context.bot.send_message(user_id,"Connecting to server has been canceled!")
        return ConversationHandler.END
    
    if len(command.split(" ")) != 1:
        print(len(command.strip(" ")))
        await context.bot.send_message(user_id,"Invalid username, try again or 'c' to cancel or 'h' to help:")
        return None
    
    context.user_data['username'] = command
    await context.bot.send_message(user_id,"Please enter Password (You message will be deleted due to your privacy):")
    return PASSWORD

# Entering Password
async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Remembers Bot user's data to update and send to functions
    user_id = update.effective_user.id
    command = update.message.text.strip()

    if command == 'c':
        await context.bot.send_message(user_id,"Connecting to server has been canceled!")
        return ConversationHandler.END
        
    context.user_data['password'] = command
    context.user_data['port'] = 22
    await context.bot.send_message(user_id,f'''Connecting to {context.user_data['IP']} via ssh port {context.user_data['port']}.
Enter:
1 to confirm
port number to specify port
c to cancel connection''')
    await update.message.delete()
    return CONFIRM_SSH

async def ssh_connection_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Remembers Bot user's data to update and send to functions
    user_id = update.effective_user.id
    command = update.message.text.strip()
    if command == '1':
        await context.bot.send_message(user_id,"Connecting to server.......")
        context.user_data["ssh_session"] = start_ssh_session(user_id, {"ssh_host": context.user_data['IP'], "ssh_user": context.user_data['username'], "ssh_pass": context.user_data['password']})
        await update.message.reply_text("Connected! Send commands to execute. Send /stop to close session.")
        return SESSION
    elif command == 'c':
        await context.bot.send_message(user_id,"Connecting to server has been canceled!")
        return ConversationHandler.END
    else:
        try:
            port = int(command)
            context.user_data['port'] = port
            await context.bot.send_message(user_id,f'''Connecting to {context.user_data['IP']} via ssh port {context.user_data['port']}.
Enter:
1 to confirm
port number to specify port
c to cancel connection
''')
            return None
        except:
            await context.bot.send_message(user_id,f'''Invalid input!
Connecting to {context.user_data['IP']} via ssh port {context.user_data['port']}.
Enter:
1 to confirm
port number to specify port
c to cancel connection
''')
            return None
    
async def ssh_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = context.user_data["ssh_session"]

    # send command
    command = update.message.text + "\n"
    session["channel"].send(command)

    # wait for output
    time.sleep(0.5)

    output = session["buffer"]["data"]
    session["buffer"]["data"] = ""   # clear after reading
    output = clean_output(output)

    if not output.strip():
        output = "(no output)"

    if len(output) > 4000:
        output = output[:4000] + "\n...output truncated..."

    await update.message.reply_text(f"<pre>{output}</pre>", parse_mode="HTML")
    return SESSION


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
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
            CONFIRM_SSH: [MessageHandler(filters.TEXT & ~filters.COMMAND, ssh_connection_confirm)],
            SESSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ssh_command)],
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