FROM debian:buster

RUN apt update -y && \
    apt upgrade -y && \
    apt install -y python3-pip python3-dev python3-venv autoconf libssl-dev libxml2-dev libxslt1-dev libjpeg-dev libffi-dev libudev-dev zlib1g-dev pkg-config libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libavresample-dev libavfilter-dev ffmpeg git

RUN git clone https://github.com/home-assistant/core.git /src/core && \
    cd /src/core && \
    script/setup && \
    cd /

EXPOSE 8123

ADD devenv-entrypoint.sh /
