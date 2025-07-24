import logging

import logging_loki
from decouple import config

LOKI_URL = config("LOKI_URL", default="http://loki:3100/loki/api/v1/push")
handler = logging_loki.LokiHandler(
    url=LOKI_URL,
    tags={"application": "telegram-bot"},
    version="1",
)
def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
