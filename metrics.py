# -*- coding: utf-8 -*-
import datetime
import os

from elasticsearch import Elasticsearch

import termin

es = Elasticsearch([{'host': os.getenv("ELASTIC_HOST"), 'port': 9200}],
                   http_auth=(os.getenv('ELASTIC_USER'), os.getenv('ELASTIC_PASS')), )


def log_search(user: int, buro: termin.Buro, appointment: str):
    e1 = {
        "timestamp": datetime.datetime.utcnow(),
        "user": int(user),
        "buro": str(buro),
        "termin": appointment
    }
    es.index(index='munich-tg-queries', body=e1)


def log_result(buro: termin.Buro, place: str, appointment: str, free_in: int = 999999, amount=0):
    e1 = {
        "timestamp": datetime.datetime.utcnow(),
        "place": place,
        "buro": str(buro),
        "termin": appointment,
        "free_in": free_in,
        "amount": amount
    }
    es.index(index='munich-tg-results', body=e1)


def log_subscription(buro: termin.Buro, appointment: str, user: int, interval:int):
    e1 = {
        "timestamp": datetime.datetime.utcnow(),
        "user": int(user),
        "buro": str(buro),
        "termin": appointment,
        "interval": int(interval)
    }
    es.index(index='munich-tg-subscriptions', body=e1)
