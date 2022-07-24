FROM python:3.9

RUN mkdir /app

COPY requirements.txt /app

WORKDIR /app
RUN pip install -r requirements.txt

ADD . /app

CMD python /app/tg_bot.py