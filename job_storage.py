# -*- coding: utf-8 -*-
import datetime

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

import printers
import utils
from metrics import MetricCollector

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
}
scheduler = BackgroundScheduler(jobstores=jobstores)


def clear_jobs():
    logger = utils.get_logger()
    logger.info("Cleaning jobs...")

    # remove jobs scheduled more than a week ago
    for job in scheduler.get_jobs():
        if 'created_at' in job.kwargs and (datetime.datetime.now() - job.kwargs['created_at']).days >= 7:
            logger.info("Removing job %s" % job.kwargs['chat_id'], extra={'user': job.kwargs['chat_id']})
            remove_subscription(job.kwargs['chat_id'], automatic=True)


def init_scheduler():
    scheduler.start()
    if not scheduler.get_job('cleanup'):
        scheduler.add_job(clear_jobs, "interval", minutes=30, id="cleanup")
    else:
        # Just to make sure interval is always correct here
        utils.get_logger().info("Rescheduling cleanup job...")
        scheduler.reschedule_job('cleanup', trigger='interval', minutes=30)


def add_subscription(update, context, interval):
    logger = utils.get_logger()
    metric_collector = MetricCollector.get_collector()

    buro = context.user_data['buro']
    termin = context.user_data['termin_type']
    chat_id = str(update.effective_chat.id)
    kwargs = {'chat_id': chat_id, 'buro': buro.get_id(), 'termin': termin, 'created_at': datetime.datetime.now()}
    scheduler.add_job(printers.notify_about_termins, 'interval', kwargs=kwargs, minutes=int(interval),
                      id=chat_id)

    logger.info(f'[{chat_id}] Subscription for %s-{termin} created with interval {interval}' % buro.get_name(), extra={'user': chat_id})
    metric_collector.log_subscription(buro=buro, appointment=termin, interval=interval, user=int(chat_id))


def remove_subscription(chat_id, automatic=False):
    if not scheduler.get_job(chat_id):
        return
    scheduler.remove_job(chat_id)
    if automatic:
        utils.get_logger().info(f'[{chat_id}] Subscription removed since it\'s expired', extra={'user': chat_id})
        utils.get_bot().send_message(chat_id=chat_id,
                                     text='Subscription was removed since it was created more than a week ago')
    else:
        utils.get_logger().info(f'[{chat_id}] Subscription removed by request', extra={'user': chat_id})
        utils.get_bot().send_message(chat_id=chat_id, text='You were unsubscribed successfully')


def get_jobs():
    return scheduler.get_jobs()


def get_job(chat_id):
    return scheduler.get_job(chat_id)
