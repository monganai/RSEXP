FROM python:latest
ENV PYTHONUNBUFFERED 1
COPY . /code/
WORKDIR /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn
RUN pip install psycopg2
RUN pip install setproctitle
RUN pip install ez-pg
ENTRYPOINT ["gunicorn"]
CMD ["ridesafe-api:app"]
