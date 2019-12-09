FROM python:3.7

ADD . /benbot
WORKDIR /benbot

RUN pip install -U pip
RUN pip install -r /benbot/requirements.txt

EXPOSE 8080
ENV PYTHONPATH="$PYTHONPATH:/benbot/.."

CMD [ "/usr/local/bin/python", "benbot5.py" ]
