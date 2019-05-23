FROM python:3.7

RUN mkdir /termin

COPY requirements.txt /termin

WORKDIR /termin
RUN pip install -r requirements.txt

ADD . /termin

CMD python /termin/tg_bot.py