FROM python:3
ENV PYTHONUNBUFFERED=1

# RUN mkdir -p /app/envDataSystem
COPY ./envdsys /app/envDataSystem/envdsys
RUN mkdir -p /app/envDataSystem/envdsys/config
RUN mkdir -p /data/envDataSystem/UIServer

WORKDIR /app/envDataSystem/envdsys
RUN pip install -r requirements.txt

COPY ./docker/envdsys/entrypoint.sh /app/envDataSystem/envdsys/entrypoint.sh

RUN useradd envdsys
RUN chown -R envdsys:envdsys /app/envDataSystem/envdsys
RUN chown -R envdsys:envdsys /data/envDataSystem/UIServer

USER envdsys

VOLUME ["/app/envDataSystem/envdsys/config", "/data/envDataSystem/UIServer"]

# # WORKDIR /code
# # COPY requirements.txt /code/
# # RUN pip install -r requirements.txt
# # COPY . /code/
# # COPY composeexample/remove_settings.py /code/config/

CMD /bin/bash