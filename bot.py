import asyncio
from mailtmapi import MailTM
from telegram import *
from telegram.ext import *
from telegram._update import *
import logging
import requests

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
#--------------------------------------------------------------------------------------------------------------
async def email_delete(accId,token):
    mailtm = MailTM()
    state = await mailtm.delete_account_by_id(accId,token)
    await mailtm.session.close()
    return state

async def email_gen():
    mailtm = MailTM()
    mail = await mailtm.get_account()
    await mailtm.session.close()
    return mail

async def get_msgs_btn(mailToken):
    btn_list = []
    mailtm = MailTM()
    data = await mailtm.get_messages(mailToken)
    msgs = data.hydra_member
    await mailtm.session.close()
    if(len(msgs) > 0):
        for msg in msgs:
            btn_list.append([InlineKeyboardButton(f"{msg.from_.name}[{msg.subject}]",callback_data=msg.id)])

    btn_list.append([InlineKeyboardButton("Refresh 🔄",callback_data="refresh")])
    return InlineKeyboardMarkup(btn_list)
    
async def get_msg_by_id(msg_id,token):
    response = requests.get(f"https://api.mail.tm/messages/{msg_id}",
                                          headers={'Authorization': f'Bearer {token}'})
    if response.status_code == 200:
        msg = response.json()
        return f"Name: {msg['from']['name']}\nFrom: {msg['from']['address']}\nSubject: {msg['subject']}\n{msg['text']}"
    else:
        return "Error"
     
#-----------------------------------------------------------------------------------------------------------------
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[KeyboardButton("➕ Generate New / Delete")]]
    await update.message.reply_text("🧡 Wellcome to Temp Mail bot.",reply_markup=ReplyKeyboardMarkup(keyboard,resize_keyboard=True))

async def new_mail(update:Update,context:ContextTypes.DEFAULT_TYPE) -> None:
    mail = await email_gen()
    context.user_data["address"] = mail.address
    context.user_data["mailId"] = mail.id
    context.user_data["token"] = mail.token.token
    key = await get_msgs_btn(context.user_data["token"])
    await update.message.reply_text(f"Email: `{mail.address}` \nInbox :",parse_mode=constants.ParseMode.MARKDOWN_V2,reply_markup=key)

async def callback_checker(update:Update,context:ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if ("token" in context.user_data):    
        if (query.data == "refresh"):
            key = await get_msgs_btn(context.user_data["token"])
            try:
                await query.edit_message_reply_markup(key)
            except:
                await query.answer("No New Message Found!")
        elif (query.data == "back"):
            key = await get_msgs_btn(context.user_data["token"])
            await query.edit_message_text(f"Email: `{context.user_data['address']}` \nInbox :",parse_mode=constants.ParseMode.MARKDOWN_V2,reply_markup=key)
        else:
            try:
                msg = await get_msg_by_id(query.data,context.user_data["token"])
                key = InlineKeyboardMarkup([[InlineKeyboardButton("Back to Inbox 🔙",callback_data="back")]])
                await query.edit_message_text(msg,reply_markup=key)
            except:
                await query.answer("Somthing went wrong!")
    else:
            await query.answer("No Mail Found!")

def main():
    BOTTOKEN = input("Enter your telegram bot api token:\n")
    app = ApplicationBuilder().token(BOTTOKEN).build() 

    app.add_handler(CommandHandler("start",start))
    app.add_handler(MessageHandler(filters.Regex("^➕ Generate New / Delete$"),new_mail))
    app.add_handler(CallbackQueryHandler(callback_checker))

    app.run_polling()

if __name__ == '__main__':
    main()