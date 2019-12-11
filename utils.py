# -*- coding: utf-8 -*-
import logging
import os
from cmreslogging.handlers import CMRESHandler
from telegram import Bot
from telegram.utils.request import Request


def get_logger():
    # Enable logging
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)
    if os.getenv('ELASTIC_HOST') and os.getenv('ELASTIC_USER') and os.getenv('ELASTIC_PASS'):
        handler = CMRESHandler(hosts=[{'host': os.getenv('ELASTIC_HOST'), 'port': 9200}],
                               auth_type=CMRESHandler.AuthType.BASIC_AUTH,
                               auth_details=(os.getenv('ELASTIC_USER'), os.getenv('ELASTIC_PASS')),
                               es_index_name="munich-tg-logs",
                               index_name_frequency=CMRESHandler.IndexNameFrequency.MONTHLY)
        logger.addHandler(handler)
    return logger


def get_bot():
    # Default size from the library, 4 workers + 4 additional
    request = Request(con_pool_size=8)
    return Bot(token=os.getenv("TG_TOKEN"), request=request)


def get_min_interval():
    return int(os.getenv("MIN_CHECK_INTERVAL_MINUTES", 15))
