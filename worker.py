# -*- coding: utf-8 -*-
import datetime

import termin_api
import utils
from metrics import MetricCollector
from termin_api import Buro

logger = utils.get_logger()
metric_collector = MetricCollector.get_collector()


def get_available_appointments(department: Buro, termin_type, user_id=0):
    logger.info(f'[{user_id}] Query for <{termin_type}> at %s' % department.get_name(), extra={'user': user_id})
    metric_collector.log_search(user=user_id, buro=department, appointment=termin_type)

    appointments = termin_api.get_termins(department, termin_type)
    if appointments is None:
        logger.error(
            f'Seems like appointment title <{termin_type}> is not accepted by the '
            f'buro <%s> any more:' % department.get_name(), extra={'user': user_id})
        return None

    # list of tuples: (caption, date, time)
    available_appointments = []
    for k, v in appointments.items():
        caption = v['caption']
        first_date = None
        for date in v['appoints']:
            if v['appoints'][date]:
                first_date = date

                next_in = (datetime.datetime.strptime(first_date, '%Y-%m-%d').date() - datetime.date.today()).days
                logger.info(f'[{user_id}] Soonest appt at {caption} is {next_in} days from today',
                            extra={'user': user_id})
                metric_collector.log_result(department, caption, termin_type, next_in, amount=len(v['appoints'][date]))

                break

        if first_date:
            available_appointments.append((caption, first_date, v['appoints'][first_date]))

    if not available_appointments:
        metric_collector.log_result(department, place="", appointment=termin_type)

    return available_appointments
