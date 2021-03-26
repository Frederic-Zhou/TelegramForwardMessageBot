import logging
import getpass
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, message
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram.utils import helpers
from urllib.parse import quote
from datetime import datetime
import atexit
import pickle
import os
# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# 定义全局变量
MYID = ""  # 自己的chatID
TOKEN = ""  # 机器人的token
CURRENTMESSAGE = ""  # 当前发出的消息对象
CURRENCHAT = ""  # 需要转发的对话ID
CHATSLIST = {}
KEYWORDS = []
ISKEYWORDSNOTIFY = False
# 定义全局变量结束


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        'Hi! I am online, I will forward your all messages', disable_notification=True)


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    global KEYWORDS
    text = 'Help!, I will forward your all messages'
    text += "\n是否根据关键字提醒?%s" % ISKEYWORDSNOTIFY
    text += "\n关键字:\n%s" % " ".join(KEYWORDS)
    text += "\n添加关键字 /addkeywords (用空格分割)"
    text += "\n清空关键字 /clearkeywords"
    text += "\n切换关键字提醒 /tagglekeywordsnotify"

    update.message.reply_text(text, disable_notification=True)


def addkeywords_command(update: Update, context: CallbackContext) -> None:
    global KEYWORDS
    kw = update.message.text
    if len(kw) > 0:
        kwarr = kw.split(" ")
        KEYWORDS += kwarr[1:]

    update.message.reply_text("关键字:\n%s" % " ".join(
        KEYWORDS), disable_notification=True)


def clearkeywords_command(update: Update, context: CallbackContext) -> None:
    global KEYWORDS
    KEYWORDS = []
    update.message.reply_text("关键字:\n%s" % " ".join(
        KEYWORDS), disable_notification=True)


def tagglekeywordsnotify_command(update: Update, context: CallbackContext) -> None:
    global ISKEYWORDSNOTIFY
    ISKEYWORDSNOTIFY = not ISKEYWORDSNOTIFY
    update.message.reply_text("是否关键字提醒:%s" %
                              ISKEYWORDSNOTIFY, disable_notification=True)


def forwardToMe(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    global CHATSLIST
    global CURRENCHAT
    global CURRENTMESSAGE
    global ISKEYWORDSNOTIFY
    # notify(update)
    print(update.message)
    # 如果是自己消息
    if update.message.chat.id == MYID:

        CURRENTMESSAGE = update.message

        # 如果当前ChatID不是空，说明已经选择了一个ChatID，直接发送
        if CURRENCHAT != "":
            msg = update.message.bot.forward_message(
                chat_id=CURRENCHAT,
                from_chat_id=CURRENTMESSAGE.chat.id,
                message_id=CURRENTMESSAGE.message_id)

            # 回复提示，并添加一个撤回按钮
            update.message.reply_text(text=f"发送到: {CHATSLIST[CURRENCHAT][0]}",
                                      disable_notification=True,
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                                          "Backout It!", callback_data="%s|%s" % (msg.chat.id, msg.message_id))]]))
            CURRENTMESSAGE = ""
            CURRENCHAT = ""  # 发送完后重制当前会话
        else:
            # 否则，回复一个询问，选择要发送的ChatID
            sorted_key = sorted(
                CHATSLIST, key=lambda x: CHATSLIST[x][1], reverse=False)

            if len(CHATSLIST.keys()) > 0:
                keyboard = []
                for key in sorted_key:
                    keyboard.append(
                        [InlineKeyboardButton(
                            CHATSLIST[key][0], callback_data=key)]
                    )

                update.message.reply_text(
                    '选择一个对话/组:', disable_notification=True, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                update.message.reply_text(
                    '没有活跃的对话', disable_notification=True)
                CURRENTMESSAGE = ""
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
            disable_notification=ISKEYWORDSNOTIFY and
            not containsKeyWords(update.message.text),
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

    # 如果按钮值是一个数组，说明是删除消息操作
    if (len(query.data.split("|")) > 1):

        chatid = query.data.split("|")[0]
        msgid = query.data.split("|")[1]
        query.bot.delete_message(chatid, msgid)

        query.edit_message_text(text=f"已删除消息: {CHATSLIST[chatid][0]}")
        return
    # 如果当前消息不为空，那么直接发送消息到选择的ChatID
    if CURRENTMESSAGE != "":

        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery

        msg = query.bot.forward_message(
            chat_id=query.data,
            from_chat_id=CURRENTMESSAGE.chat.id,
            message_id=CURRENTMESSAGE.message_id)
        CURRENCHAT = ""
        CURRENTMESSAGE = ""  # 发送完后，当前消息重制为空

        # 反馈一下，并且添加一个是否删除消息的按钮
        query.edit_message_text(text=f"发送到: {CHATSLIST[query.data][0]}",
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                                     "Backout It!", callback_data="%s|%s" % (msg.chat.id, msg.message_id))]]))

    else:
        # 否则，记录下选择的ChatID
        query.edit_message_text(text=f"正在等待回复: {CHATSLIST[query.data][0]}")
        CURRENCHAT = query.data


def containsKeyWords(str):
    global KEYWORDS

    if len(KEYWORDS) > 0:
        for kw in KEYWORDS:
            if (kw in str):
                return True
    return False


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
    dispatcher.add_handler(CommandHandler("addkeywords", addkeywords_command))
    dispatcher.add_handler(CommandHandler(
        "clearkeywords", clearkeywords_command))
    dispatcher.add_handler(CommandHandler(
        "tagglekeywordsnotify", tagglekeywordsnotify_command))

    dispatcher.add_handler(CallbackQueryHandler(button))
    # on noncommand i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(~Filters.command, forwardToMe))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


def LoadCHATLIST():
    global CHATSLIST
    try:
        f = open('chatlist', 'rb')
        CHATSLIST = pickle.load(f)
        f.close()
    except:
        print("load fail")


@atexit.register
def SaveCHATSLIST():
    global CHATSLIST
    f = open('chatlist', 'wb')
    pickle.dump(CHATSLIST, f)
    f.close()
    print("saved")


if __name__ == '__main__':
    try:
        MYID = getpass.getpass("ChatID[隐藏模式]:")
        print("Chat ID: %s***%s" % (MYID[:2], MYID[-2:]))
        MYID = int(MYID)
        TOKEN = getpass.getpass("Token[隐藏模式]:")
        print("Token: %s***:******%s" % (TOKEN[:2], TOKEN[-2:]))
    except:
        print("输入正确的ChatID")
        os._exit(0)

    try:
        LoadCHATLIST()
        main()
    except KeyboardInterrupt:
        pass


# todo
# 1. 撤回消息啊
