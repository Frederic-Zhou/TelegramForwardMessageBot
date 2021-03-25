import logging
import getpass
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, message
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram.utils import helpers
from urllib.parse import quote
from datetime import datetime
# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


MYID = getpass.getpass("转发目标的ChatID[隐藏模式]:")
print("Chat ID: %s***%s" % (MYID[:2], MYID[-2:]))
TOKEN = getpass.getpass("输入Bot的Token[隐藏模式]:")
print("Token: %s***:******%s" % (TOKEN[:2], TOKEN[-2:]))

# 转换成数字
MYID = int(MYID)

CURRENTMESSAGE = ""
CURRENCHAT = ""
CHATSLIST = {}


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        'Hi! I am online, I will forward your all messages')


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!, I will forward your all messages')


def forwardToMe(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    global CHATSLIST
    global CURRENCHAT
    global CURRENTMESSAGE
    # notify(update)
    print(update.message)
    # 如果是自己消息
    if update.message.chat.id == MYID:

        CURRENTMESSAGE = update.message

        if CURRENCHAT != "":
            update.message.bot.forward_message(
                chat_id=CURRENCHAT,
                from_chat_id=CURRENTMESSAGE.chat.id,
                message_id=CURRENTMESSAGE.message_id)
            CURRENTMESSAGE = ""
            CURRENCHAT = ""  # 发送完后重制当前会话
        else:
            #CHATSLIST_sorted = sorted(CHATSLIST.items(), key=lambda x: x[1])
            sorted_key = sorted(
                CHATSLIST, key=lambda x: CHATSLIST[x][1], reverse=True)

            if len(CHATSLIST.keys()) > 0:
                keyboard = []
                for key in sorted_key:
                    keyboard.append(
                        [InlineKeyboardButton(
                            CHATSLIST[key][0], callback_data=key)]
                    )

                update.message.reply_text(
                    '选择一个对话/组:', reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                update.message.reply_text(
                    '没有活跃的对话')
            pass
    else:
        # 非本人消息，直接转发
        # 保存对话信息
        CHATSLIST[f'{update.message.chat.id}'] = ["%s" % (
            "「%s」" % update.message.chat.title if update.message.chat.title else "%s%s%s" % (
                " %s" % update.message.from_user.first_name if update.message.from_user.first_name else "",
                " %s" % update.message.from_user.last_name if update.message.from_user.last_name else "",
                " @%s" % update.message.from_user.username if update.message.from_user.username else ""
            )),
            datetime.timestamp(datetime.now())]

        # 转发到本人账号
        update.message.bot.forward_message(
            chat_id=MYID,
            from_chat_id=update.message.chat.id,
            message_id=update.message.message_id)

        # 再发送一条来源消息
        content = "%s:%s%s%s%s" % (
            update.message.chat.type,
            "「%s」" % update.message.chat.title if update.message.chat.title else "",
            " %s" % update.message.from_user.first_name if update.message.from_user.first_name else "",
            " %s" % update.message.from_user.last_name if update.message.from_user.last_name else "",
            " @%s" % update.message.from_user.username if update.message.from_user.username else ""
        )

        update.message.bot.send_message(
            chat_id=MYID,
            disable_notification=True,  # 来源消息不提醒
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                "Reply It", callback_data=update.message.chat.id)]]),
            text=content
        )


def button(update: Update, context: CallbackContext) -> None:

    global CURRENTMESSAGE
    global CHATSLIST
    global CURRENCHAT

    query = update.callback_query

    query.answer()
    if CURRENTMESSAGE != "":

        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        query.edit_message_text(text=f"发送到: {CHATSLIST[query.data][0]}")
        query.bot.forward_message(
            chat_id=query.data,
            from_chat_id=CURRENTMESSAGE.chat.id,
            message_id=CURRENTMESSAGE.message_id)
        CURRENCHAT = ""
        CURRENTMESSAGE = ""  # 发送完后，当前消息重制为空
    else:
        # 保存当前对话
        query.edit_message_text(text=f"正在等待回复: {CHATSLIST[query.data][0]}")
        CURRENCHAT = query.data


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # updater = None
    try:
        updater = Updater(TOKEN)
    except:
        print("bot token错误")
        return

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(CallbackQueryHandler(button))
    # on noncommand i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(~Filters.command, forwardToMe))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
