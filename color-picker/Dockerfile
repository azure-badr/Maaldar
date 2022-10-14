FROM python:3.9

RUN pip install hypercorn discord quart psycopg2

COPY . .

EXPOSE 80

CMD python main.py

