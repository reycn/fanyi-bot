#!/usr/bin/python3.7
import re
from configparser import ConfigParser
from sys import path as syspath

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import (InlineKeyboardButton, InlineQuery,
                           InlineQueryResultArticle, InputTextMessageContent)
from loguru import logger
from sentry_sdk import capture_message, init

from api.balancer import trans
from tool.clean import filter_bot
from tool.detect import is_command, lang

# 初始化 bot
try:
    cfg = ConfigParser()
    cfg.read(syspath[0] + '/config/config.ini')
    API_TOKEN = cfg.get('bot', 'token')
    ADMIN_ID = cfg.get('bot', 'admin')
    SENTRY_SDK = cfg.get('sentry', 'sdk')
    GROUP_LIST = [] if cfg.get('group', 'custom') == 'None' else cfg.get(
        'group', 'enabled').split(',')
    GROUP_LIST_CUSTOM = [] if cfg.get(
        'group', 'custom') == 'None' else cfg.get('group', 'custom').split(',')
    LANG = cfg.get('lang', 'destination')  # 暂时没有使用

except Exception as e:
    logger.exception("Config:" + str(e))
    capture_message('Config: ' + str(e))
    exit()

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
init(SENTRY_SDK, traces_sample_rate=1.0)

delete_btn = types.InlineKeyboardMarkup(resize_keyboard=True, selective=True)
delete_btn.insert(InlineKeyboardButton(text='🗑️', callback_data='delete'))

# 定义函数


@dp.callback_query_handler(text='delete')
async def _(call: types.CallbackQuery):
    try:
        await call.message.delete()
        await call.answer(text="该消息已删除")
    except Exception as e:
        logger.exception("Delete:" + str(e))
        capture_message('Delete: ' + str(e))


def query(text: str, to_lang: str = None) -> str:  # type: ignore
    try:
        if to_lang == None:
            if lang(text) == 'zh':
                to_lang = 'en'
            elif lang(text) == 'en':
                to_lang = 'zh'
            else:
                to_lang = 'zh'
        else:
            pass
        result = trans(text, to_lang)
        return result
    except Exception as e:
        logger.exception("Query:")
        capture_message('Query: ' + str(e))


def translate_msg(
        message: types.Message,
        offset: int = 0,
        lang: str = None,  # type: ignore
        pattern: str = None) -> str:  # type: ignore
    if message.reply_to_message:  # 如果是回复则取所回复消息文本
        text = message.reply_to_message.text
    else:  # 如果不是回复则取命令后文本
        text = message.text[offset:]  # 去除命令文本
    try:
        text = filter_bot(text)
    except:
        pass

    text = re.sub(pattern, '', text) if pattern else text
    if len(text) == 0:
        if message.reply_to_message:
            logger_msg(message)
            result = query(text, to_lang=lang)
            return result
        else:
            result = '''忘记添加需要翻译的文本？请在命令后添加需要翻译的话，例如：
/en 你好
'''
            return \
                result
    else:
        logger_msg(message)
        result = query(text, to_lang=lang)
        # logger.info(result)
        return \
            result


def translate_auto(
        message: types.Message,
        offset: int = 0,
        lang: str = None,  # type: ignore
        pattern: str = None) -> str:  # type: ignore
    if message.reply_to_message and (len(
            re.sub(
                r'^(translate|trans|tran|翻译|中文|Chinese|zh|英文|英语|English|en)',
                "", message.text)) <= 1):  # 如果是回复则取所回复消息文本
        text = message.reply_to_message.text
    else:  # 如果不是回复则取命令后文本
        text = message.text[offset:]  # 去除命令文本
    text = text.replace('@fanyi_bot', '').strip()
    if pattern:
        text = re.sub(pattern, '', text)
    if len(text) == 0:
        if message.reply_to_message:
            logger_msg(message)
            result = query(text)
            return result
        else:
            result = '''忘记添加需要翻译的文本？请在命令后添加需要翻译的话，例如：

/en 你好
'''
            return \
                result
    else:
        logger_msg(message)
        result = query(text)
        # logger.info(result)
        return result


def logger_msg(message: types.Message) -> None:
    chat_type = message.chat.type
    user = message.from_user.username
    user_id = message.from_user.id
    group = message.chat.title
    group_id = message.chat.id
    chat_name = message.chat.username or message.from_user.username
    if group:
        log_msg = f'[{chat_type}, %{group}, %{group_id}, &{chat_name}, \\@{user}, #{user_id}] {message.text}'
        logger.info(log_msg)
    else:
        log_msg = f'[{chat_type}, @{chat_name}, #{user_id}] {message.text} '
        logger.info(log_msg)


####################################################################################################
# 欢迎词
@dp.message_handler(commands=['start', 'welcome', 'about', 'help'])
async def command_start(message: types.Message) -> None:
    intro = '''使用说明：
- 私聊机器人，自动翻译文字消息；
- 群聊中添加机器人，使用命令翻译指定消息；
- 任意聊天框，输入 @fanyi_bot 实时翻译。

使用样例：
/fy 检测语言并翻译
/zh Translate a sentence into Chinese.
/en 翻译到英文

最近更新
- [2020.11.14] 修复了一个上游引起的 BUG

加入群组 @fanyi_group 参与讨论。'''
    await bot.send_chat_action(message.chat.id, action="typing")
    await message.answer(intro)


####################################################################################################
# 翻译命令
####################################################################################################
# 中英文
@dp.message_handler(commands=['fy', 'tr', '翻译'])
async def command_fy(message: types.Message) -> None:
    await bot.send_chat_action(message.chat.id, action="typing")
    result = translate_msg(message, 3)  # None -> Chinese + English
    await message.reply(result, reply_markup=delete_btn)


# 中文
@dp.message_handler(commands=['zh'])
async def command_zh(message: types.Message) -> None:
    await bot.send_chat_action(message.chat.id, action="typing")
    result = translate_msg(message, 3, 'zh')
    await message.reply(result, reply_markup=delete_btn)


# 英文
@dp.message_handler(commands=['en'])
async def command_en(message: types.Message) -> None:
    await bot.send_chat_action(message.chat.id, action="typing")
    result = translate_msg(message, 3, 'en')
    await message.reply(result, reply_markup=delete_btn)


@dp.message_handler(commands=['id'])
async def command_id(message: types.Message) -> None:
    await bot.send_chat_action(message.chat.id, action="typing")
    result = str(message.chat.id)
    await message.reply(result, reply_markup=delete_btn)


# @logger.catch()
@dp.message_handler(commands=['auto'])
async def command_enable_auto_translation(
        message: types.Message,
        GROUP_LIST_CUSTOM: list = GROUP_LIST_CUSTOM) -> None:
    await bot.send_chat_action(message.chat.id, action="typing")
    if str(message.chat.id) in GROUP_LIST_CUSTOM or str(
            message.chat.id) in GROUP_LIST:
        await message.reply('已经是启用状态 / Already enabled',
                            reply_markup=delete_btn)
    else:
        try:
            # logger.info(type(GROUP_LIST_CUSTOM))
            GROUP_LIST_CUSTOM.append(str(message.chat.id))
            cfg = ConfigParser()
            cfg_path = syspath[0] + '/config/config.ini'
            cfg.read(cfg_path)
            cfg.set('group', 'custom', ','.join(GROUP_LIST_CUSTOM))
            with open(cfg_path, 'w') as configfile:
                cfg.write(configfile)
            await message.reply('自动翻译已启动 / Auto-translation enabled',
                                reply_markup=delete_btn)
        except Exception as e:
            logger.warning('Failed:' + str(e))
            await message.reply('自动翻译启动失败 / Auto-translation enabling failed',
                                reply_markup=delete_btn)


# @logger.catch()
@dp.message_handler(commands=['not'])
async def command_disable_auto_translation(
        message: types.Message,
        GROUP_LIST_CUSTOM: list = GROUP_LIST_CUSTOM) -> None:
    await bot.send_chat_action(message.chat.id, action="typing")
    if str(message.chat.id) in GROUP_LIST_CUSTOM:
        await message.reply('已经是关闭状态 / Already disabled',
                            reply_markup=delete_btn)
    else:
        try:
            GROUP_LIST_CUSTOM.remove(str(message.chat.id))
            cfg = ConfigParser()
            cfg_path = syspath[0] + '/config/config.ini'
            cfg.read(cfg_path)
            cfg.set('group', 'custom', ','.join(GROUP_LIST_CUSTOM))
            with open(cfg_path, 'w') as configfile:
                cfg.write(configfile)
            await message.reply('自动翻译已关闭 / Auto-translation disabled',
                                reply_markup=delete_btn)
        except Exception as e:
            logger.warning('Failed:' + str(e))
            await message.reply('自动翻译关闭失败 / Auto-translation disabling failed',
                                reply_markup=delete_btn)


####################################################################################################
# 自然指令
####################################################################################################
@dp.message_handler(regexp='^(translate|trans|tran|翻译) ')
async def keyword_fy(message: types.Message) -> None:
    result = translate_msg(message, pattern='^(translate|trans|tran|翻译) ')
    await bot.send_chat_action(message.chat.id, action="typing")
    await message.reply(result, reply_markup=delete_btn)


@dp.message_handler(regexp='^(英文|英语|English|en) ')
async def keyword_en(message: types.Message) -> None:
    result = translate_msg(message, lang='en', pattern='^(英文|英语|English|en) ')
    await bot.send_chat_action(message.chat.id, action="typing")
    await message.reply(result, reply_markup=delete_btn)


@dp.message_handler(regexp='^(中文|Chinese|zh) ')
async def keyword_zh(message: types.Message) -> None:
    result = translate_msg(message, lang='zh', pattern='^(中文|Chinese|zh) ')
    await bot.send_chat_action(message.chat.id, action="typing")
    await message.reply(result, reply_markup=delete_btn)


@dp.message_handler(regexp='^(translate|trans|tran|翻译)')
async def reply_keyword_fy(message: types.Message) -> None:
    if message.reply_to_message:
        result = translate_msg(message, pattern='^(translate|trans|tran|翻译)')
        await bot.send_chat_action(message.chat.id, action="typing")
        await message.reply(result, reply_markup=delete_btn)


@dp.message_handler(regexp='^(英文|English|en)')
async def reply_keyword_en(message: types.Message) -> None:
    if message.reply_to_message:
        result = translate_msg(message, lang='en', pattern='^(英文|English|en)')
        await bot.send_chat_action(message.chat.id, action="typing")
        await message.reply(result, reply_markup=delete_btn)


@dp.message_handler(regexp='^(中文|Chinese|zh)')
async def reply_keyword_zh(message: types.Message) -> None:
    if message.reply_to_message:
        result = translate_msg(message, lang='zh', pattern='^(中文|Chinese|zh)')
        await bot.send_chat_action(message.chat.id, action="typing")
        await message.reply(result, reply_markup=delete_btn)


####################################################################################################
# 私聊自动检测语言并翻译
####################################################################################################


@dp.callback_query_handler(text='translate')
async def query_translate(call: types.CallbackQuery) -> None:
    origin_msg = call.message.text.split('▸')[1].split('\n')[0]
    translated_msg = call.message.text.split('▸')[-1]
    # await bot.send_chat_action(message.chat.id, action="typing")
    await call.answer(text="消息已翻译 Message translated")
    await bot.edit_message_text("`" + call.message.text.split('▸')[0] + "`" + \
        query(translated_msg), call.message.chat.id, call.message.message_id,
        parse_mode="markdown")


@dp.callback_query_handler(text=['zh', 'en', 'ja', 'ru', 'vi'])
async def query_specify(call: types.CallbackQuery) -> None:
    languages = {'zh': '⚙️', 'en': '⚙️', 'ja': '⚙️', 'ru': '⚙️', 'vi': '⚙️'}
    # await bot.send_chat_action(message.chat.id, action="typing")
    reply_message = call.message.reply_to_message
    reply_text = reply_message.text
    action_btn = types.InlineKeyboardMarkup(resize_keyboard=True,
                                            selective=True)
    action_btn.insert(
        InlineKeyboardButton(text=f'{languages[call.data]}',
                             callback_data='select'))
    action_btn.insert(InlineKeyboardButton(text='🗑️', callback_data='del'))

    logger.info('\n\n')
    log_msg = f"[Group] {reply_message.chat.title}({reply_message.chat.id})"
    logger.info(log_msg)
    try:
        await call.answer(text=f"正在翻译 Translating...")
        await bot.edit_message_text(query(reply_text, call.data),
                                    call.message.chat.id,
                                    call.message.message_id,
                                    parse_mode="markdown",
                                    reply_markup=action_btn)
    except Exception as e:
        logger.exception('Answer: ' + str(e))
        capture_message('Answer: ' + str(e))

    # await call.answer(text="消息已翻译 Message translated")


@dp.callback_query_handler(text='del')
async def query_delete(call: types.CallbackQuery) -> None:
    # await bot.send_chat_action(message.chat.id, action="typing")
    await call.answer(text="消息已删除 Message deleted")
    await call.message.delete()


@dp.callback_query_handler(text='select')
async def query_select(call: types.CallbackQuery) -> None:
    # await bot.send_chat_action(message.chat.id, action="typing")
    action_btn = types.InlineKeyboardMarkup(resize_keyboard=True,
                                            selective=True)
    action_btn.insert(InlineKeyboardButton(text='中文', callback_data='zh'))
    action_btn.insert(InlineKeyboardButton(text='English', callback_data='en'))
    action_btn.insert(InlineKeyboardButton(text='にほんご', callback_data='ja'))
    # action_btn.insert(InlineKeyboardButton(text='🇷🇺', callback_data='ru'))
    # action_btn.insert(InlineKeyboardButton(text='🇻🇳', callback_data='vi'))
    action_btn.insert(InlineKeyboardButton(text='🗑️', callback_data='del'))
    try:
        await call.answer(text="请选择一种语言 Please select a language")
        await bot.edit_message_text(call.message.text,
                                    call.message.chat.id,
                                    call.message.message_id,
                                    parse_mode="markdown",
                                    reply_markup=action_btn)
    except Exception as e:
        logger.exception('Answer: ' + str(e))
        capture_message('Answer: ' + str(e))


@dp.callback_query_handler(text='mute')
async def query_mute(call: types.CallbackQuery) -> None:
    origin_msg = call.message.text.split('▸')[1].split('\n')[0]
    # await bot.send_chat_action(message.chat.id, action="typing")
    try:
        await call.answer(text="显示原消息 Original message showed")
        await bot.edit_message_text(origin_msg,
                                    call.message.chat.id,
                                    call.message.message_id,
                                    parse_mode="markdown")
    except Exception as e:
        logger.exception('Answer: ' + str(e))
        capture_message('Answer: ' + str(e))


####################################################################################################
# 群聊/私聊
####################################################################################################


@dp.message_handler(content_types=types.message.ContentType.TEXT)
async def text_translate(message: types.Message,
                         GROUP_LIST_CUSTOM: list = GROUP_LIST_CUSTOM) -> None:
    chat_type = message.chat.type
    chat_id = message.chat.id
    action_btn = types.InlineKeyboardMarkup(resize_keyboard=True,
                                            selective=True)
    action_btn.insert(
        InlineKeyboardButton(text='语言 Language', callback_data='select'))
    action_btn.insert(InlineKeyboardButton(text='🗑️', callback_data='delete'))
    if chat_type == 'private':
        await bot.send_chat_action(message.chat.id, action="typing")

        log_msg = f"[Private] {message.from_user.first_name}(https://t.me/{message.from_user.username}, {message.from_user.id})"
        logger.info(log_msg)
        result = query(message.text)
        try:
            await message.reply(result, disable_notification=True)
        except Exception as e:
            logger.exception('Reply: ' + str(e))
            capture_message('Reply: ' + str(e))
    elif ((chat_type == 'group') or
          (chat_type == 'supergroup')) and (str(chat_id) in GROUP_LIST or
                                            str(chat_id) in GROUP_LIST_CUSTOM):
        log_msg = f"[Group] {message.chat.title}({message.chat.id})"
        logger.info(log_msg)
        await bot.send_chat_action(message.chat.id, action="typing")
        if is_command(message.text) == False:
            result = query(message.text)
            try:
                await message.reply(result,
                                    parse_mode='markdown',
                                    disable_notification=True,
                                    disable_web_page_preview=True,
                                    reply_markup=action_btn)
            except Exception as e:
                logger.exception('Reply: ' + str(e))
                capture_message('Reply: ' + str(e))
        else:
            logger.info('PASS: a command detected')
            pass
    else:  # 过滤所有群聊、频道
        # log_msg = f"[Ignored] {message.chat.title}({message.chat.id} not enabled.)"
        # logger.debug(log_msg)
        # logger.info('PASS: group not enabled / channel')
        pass


@dp.message_handler()
async def text_others(message: types.Message) -> None:
    logger.info('Other types')
    try:
        await bot.send_chat_action(message.chat.id, action="typing")
        result = query(message.text)
    except Exception as e:
        logger.exception("Others:" + str(e))
        capture_message('Others', str(e))
        result = '? ? ?'
    await message.answer(result)


####################################################################################################
# 行内查询
####################################################################################################


@dp.inline_handler()
async def inline(inline_query: InlineQuery) -> None:
    text = inline_query.query or '输入以翻译 Input to Translate...'
    user = inline_query.from_user.username
    user_id = inline_query.from_user.id
    end_str = ''
    if len(text) >= 256:
        end_str = '\n\n(达到长度限制，请私聊翻译全文）'
    if text == '输入以翻译 Input to Translate...' or len(text) <= 2:
        pass
    else:
        # log_msg = f'[inline, @{user}, #{user_id}] {text} '
        zh_str = query(text, 'zh')
        en_str = query(text, 'en')
        # jp_str = query(text, 'ja')
        items = [
            InlineQueryResultArticle(
                id=str(0),
                title=f'{en_str.capitalize()}',
                description='English',
                input_message_content=InputTextMessageContent(
                    en_str, disable_web_page_preview=True),
            ),
            InlineQueryResultArticle(
                id=str(1),
                title=f'{zh_str.capitalize()}',
                description='中文',
                input_message_content=InputTextMessageContent(
                    zh_str, disable_web_page_preview=True),
            )
        ]

        await bot.answer_inline_query(
            inline_query.id,
            results=items,  # type: ignore
            cache_time=500)


if __name__ == '__main__':
    logger.info('Working...', )
    # executor.start_polling(dp, skip_updates=True)
    executor.start_polling(dp)
