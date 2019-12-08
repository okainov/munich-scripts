# -*- coding: utf-8 -*-
import datetime
import os

import elasticsearch

import termin_api


class MetricCollector:

    @staticmethod
    def get_collector():
        return MetricCollector(os.getenv('ELASTIC_HOST', ''), os.getenv('ELASTIC_USER', ''),
                               os.getenv('ELASTIC_PASS', ''))

    def __init__(self, host, user, password, port=9200):
        self.elastic = None
        if host and password and user and port:
            self.elastic = elasticsearch.Elasticsearch([{'host': host, 'port': port}],
                                                       http_auth=(user, password))

    def _send(self, index, body):
        if self.elastic is not None:
            self.elastic.index(index=index, body=body)

    def log_search(self, user: int, buro: termin_api.Buro, appointment: str):
        e1 = {
            "timestamp": datetime.datetime.utcnow(),
            "user": int(user),
            "buro": buro.get_name(),
            "termin": appointment
        }
        self._send(index='munich-tg-queries', body=e1)

    def log_result(self, buro: termin_api.Buro, place: str, appointment: str, free_in: int = 999999, amount=0):
        e1 = {
            "timestamp": datetime.datetime.utcnow(),
            "place": place,
            "buro": buro.get_name(),
            "termin": appointment,
            "free_in": free_in,
            "amount": amount
        }
        self._send(index='munich-tg-results', body=e1)

    def log_subscription(self, buro: termin_api.Buro, appointment: str, user: int, interval: int):
        e1 = {
            "timestamp": datetime.datetime.utcnow(),
            "user": int(user),
            "buro": buro.get_name(),
            "termin": appointment,
            "interval": int(interval)
        }
        self._send(index='munich-tg-subscriptions', body=e1)
