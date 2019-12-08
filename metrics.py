# -*- coding: utf-8 -*-
import datetime
import elasticsearch

import termin


class MetricCollector:
    def __init__(self, host, user, password, port=9200):
        self.elastic = None
        if host and password and user and port:
            self.elastic = elasticsearch.Elasticsearch([{'host': host, 'port': port}],
                                                       http_auth=(user, password))

    def _send(self, index, body):
        if self.elastic is not None:
            self.elastic.index(index=index, body=body)

    def log_search(self, user: int, buro: termin.Buro, appointment: str):
        e1 = {
            "timestamp": datetime.datetime.utcnow(),
            "user": int(user),
            "buro": str(buro),
            "termin": appointment
        }
        self._send(index='munich-tg-queries', body=e1)

    def log_result(self, buro: termin.Buro, place: str, appointment: str, free_in: int = 999999, amount=0):
        e1 = {
            "timestamp": datetime.datetime.utcnow(),
            "place": place,
            "buro": str(buro),
            "termin": appointment,
            "free_in": free_in,
            "amount": amount
        }
        self._send(index='munich-tg-results', body=e1)

    def log_subscription(self, buro: termin.Buro, appointment: str, user: int, interval: int):
        e1 = {
            "timestamp": datetime.datetime.utcnow(),
            "user": int(user),
            "buro": str(buro),
            "termin": appointment,
            "interval": int(interval)
        }
        self._send(index='munich-tg-subscriptions', body=e1)
