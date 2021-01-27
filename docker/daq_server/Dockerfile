FROM python:3
ENV PYTHONUNBUFFERED=1

# RUN mkdir -p /app/envDataSystem
COPY ./daq_server /app/envDataSystem/daq_server
COPY ./envdsys/shared /app/envDataSystem/envdsys/shared

RUN mkdir -p /app/envDataSystem/daq_server/config
RUN mkdir -p /data/envDataSystem/

WORKDIR /app/envDataSystem/daq_server
RUN pip install -r requirements.txt

COPY ./docker/daq_server/entrypoint.sh /app/envDataSystem/daq_server/entrypoint.sh

RUN useradd envdsys
RUN chown -R envdsys:envdsys /app/envDataSystem/daq_server
RUN chown -R envdsys:envdsys /data/envDataSystem/

USER envdsys

VOLUME ["/app/envDataSystem/daq_server/config", "/data/envDataSystem"]

# # WORKDIR /code
# # COPY requirements.txt /code/
# # RUN pip install -r requirements.txt
# # COPY . /code/
# # COPY composeexample/remove_settings.py /code/config/

CMD ["python", "daq_server.py"]
# CMD ["/bin/bash"]
# CMD ["python"]