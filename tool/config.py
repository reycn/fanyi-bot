from configparser import ConfigParser
from sys import path as syspath

from loguru import logger
from sentry_sdk import capture_message, init


# @logger.catch()
def config_init(
        path: str = None,  # type: ignore
        paras: str = None) -> dict or str:  # type: ignore
    if path == None:
        path = syspath[0] + '/config/config.ini'
    cfg = ConfigParser()
    cfg.read(path)
    try:
        if paras:
            configs = paras.split('.')
            return cfg.get(configs[0], configs[1])  # type: ignore
        else:
            configs = {
                'API_TOKEN': cfg.get('bot', 'token'),
                'ADMIN_ID': cfg.get('bot', 'admin'),
                'STAT': cfg.get('stat', 'enabled'),  # statistics
                'STAT_ACCOUNT': cfg.get('stat', 'account'),
                'STAT_INSTANCE': cfg.get('stat', 'instance'),
                'SENTRY_SDK': cfg.get('sentry', 'sdk'),
                'GROUP_LIST': cfg.get('group', 'enabled'),
                'LANG': cfg.get('lang', 'destination'),
                'SLEEP': float(cfg.get('bot', 'sleep'))  # useless for now
            }
            init(configs['SENTRY_SDK'], traces_sample_rate=1.0)
            return configs

    except Exception as e:
        logger.exception("Config:" + str(e))
        capture_message('Config: ' + str(e))
        exit()


if __name__ == '__main__':
    CONFIGS = config_init(None, 'bot.token')  # type: ignore
    logger.info(CONFIGS['SLEEP'])
    # executor.start_polling(dp, skip_updates=True)
