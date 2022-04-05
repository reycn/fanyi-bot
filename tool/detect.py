from re import match, search
from time import sleep

from api.google_trans_new_modified.google_trans_new import \
    google_translator
from tool.config import config_init
from loguru import logger

SLEEP = config_init(None, 'bot.sleep')  # type: ignore


def is_tradtl(text: str) -> bool:
    try:
        encoded = text.encode('big5hkscs')
        logger.info('Detected: ' + '繁体')
        return True
    except Exception as e:
        logger.info('Detected: ' + '简体')
        return False


def lang(text: str, SLEEP: float = SLEEP) -> str:  # type: ignore
    translator = google_translator()
    lang = None
    while lang == None:
        try:
            lang = translator.detect(text)[0][:2]
            # logger.info('Detect:' + lang)
        except:
            sleep(SLEEP)
            pass
    return lang


def is_command(text: str) -> bool:  # type: ignore
    pattern = r"""^\/([^\s@]+)@?(\S+)?\s?(.*)$"""
    if match(pattern, text):
        return True
    else:
        return False


if __name__ == "__main__":
    pass
