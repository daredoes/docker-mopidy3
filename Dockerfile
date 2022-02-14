FROM ubuntu:20.04

WORKDIR /media
WORKDIR /tmp
WORKDIR /config

EXPOSE 5555
EXPOSE 6600
EXPOSE 6680

# Order based on how to effectively cache docker image
RUN apt-get update
# tzdata has an interactive prompt that doesn't play nicely with docker when its a dependency
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata
RUN apt-get install -y wget git gnupg
RUN apt-get install -y python3 python3-pip
RUN apt-get install -y pkg-config libffi-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev
RUN apt-get install -y libcairo2-dev libgirepository1.0-dev
RUN apt-get install -y build-essential libasound2-dev cargo
# RUN git clone https://github.com/librespot-org/librespot /home/librespot && (cd /home/librespot && cargo build --release) && rm -rf /home/librespot
RUN wget -q -O - https://apt.mopidy.com/mopidy.gpg | apt-key add -
RUN wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/buster.list

RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y mopidy
RUN apt-get install -y mopidy-spotify
RUN apt-get install -y mopidy-soundcloud
RUN apt-get install -y mopidy-local
RUN apt-get install -y mopidy-gmusic
RUN apt-get install -y mopidy-mpd
RUN apt-get install -y mopidy-internetarchive

COPY ./requirements.txt /
RUN python3 -m pip install pycairo
RUN python3 -m pip install -r /requirements.txt

# Stuff for youtube videos
RUN apt-get install -y libmpg123-dev libmp3lame-dev gstreamer1.0-tools gstreamer1.0-alsa
# Needed for ubuntu-advantage-tools EULA
RUN echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | debconf-set-selections
RUN apt-get install -y ubuntu-restricted-extras

RUN apt-get install -y supervisor && apt-get clean
RUN mkdir -p /var/log/supervisor

COPY ./supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 9001

COPY ./start.sh /
RUN chmod +x /start.sh
COPY ./start_mopidy.sh /
RUN chmod +x /start_mopidy.sh

COPY ./start.py /
RUN chmod +x /start.py
STOPSIGNAL SIGINT

COPY ./templates /home/templates

ENTRYPOINT [ "/start.sh" ]