FROM python:3
ENV PYTHONUNBUFFERED=1

RUN apt-get update -y && apt install libusb-1.0 udev -y

# RUN mkdir -p /app/envDataSystem
# should probably changed these to links and do a wget for size reasons.
RUN mkdir -p /app/setup/lib
COPY ./daq_server/setup/deps/labjack_ljm.tar.gz /app/setup/lib/labjack_ljm.tar.gz
WORKDIR /app/setup/lib
RUN mkdir labjack_ljm \
    && tar xf labjack_ljm.tar.gz -C labjack_ljm --strip-components=1 \
    # && cd labjack_ljm \
    && labjack_ljm/labjack_ljm_installer.run -- --no-restart-device-rules \
    && rm -rf labjack_ljm

COPY ./daq_server/requirements.txt /app/setup/requirements.txt
WORKDIR /app/setup
# RUN rm -rf lib
RUN pip install -r requirements.txt

COPY ./daq_server /app/envDataSystem/daq_server
COPY ./envdsys/shared /app/envDataSystem/envdsys/shared

RUN mkdir -p /app/envDataSystem/daq_server/config
RUN mkdir -p /data/envDataSystem/

WORKDIR /app/envDataSystem/daq_server
# RUN pip install -r requirements.txt

COPY ./docker/daq_server/entrypoint.sh /app/envDataSystem/daq_server/entrypoint.sh

ARG UID
ARG GID

RUN groupadd -g $GID envdsys && useradd -u $UID -g $GID envdsys && usermod -a -G dialout envdsys
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