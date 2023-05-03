FROM ubuntu:20.04

WORKDIR /media
WORKDIR /tmp
WORKDIR /config
WORKDIR /cache
WORKDIR /data

EXPOSE 5555 6600 6680 9001

# Order based on how to effectively cache docker image
RUN apt-get update
# tzdata has an interactive prompt that doesn't play nicely with docker when its a dependency
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata
RUN apt-get install -y cron lsof supervisor wget git gnupg python3 python3-pip pkg-config libffi-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev libcairo2-dev libgirepository1.0-dev build-essential libasound2-dev
# Stuff for youtube videos
RUN apt-get install -y libmpg123-dev libmp3lame-dev gstreamer1.0-tools gstreamer1.0-alsa
# Needed for ubuntu-advantage-tools EULA
RUN echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | debconf-set-selections

RUN wget -q -O - https://apt.mopidy.com/mopidy.gpg | apt-key add -
RUN wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/buster.list

RUN apt-get update --allow-insecure-repositories
RUN apt-get -y upgrade
RUN apt-get install -y --allow-unauthenticated mopidy mopidy-local mopidy-mpd
RUN apt-get install -y --fix-missing ubuntu-restricted-extras

COPY ./requirements.txt /
RUN python3 -m pip install pycairo
RUN python3 -m pip install -r /requirements.txt

RUN apt-get install -y  && apt-get clean
RUN mkdir -p /var/log/supervisor

COPY ./supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN export IRIS_DIR=$(pip3 show mopidy_iris | grep Location: | sed 's/^.\{10\}//') && echo "mopidy ALL=(ALL) NOPASSWD: $IRIS_DIR/mopidy_iris/system.sh" >> /etc/sudoers

# Add crontab file in the cron directory
COPY ./cronjob /etc/cron.d/cronjob

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/cronjob

# Apply cron job
RUN crontab /etc/cron.d/cronjob
# An empty line is required at the end of this file for a valid cron file.

COPY ./start.sh /
RUN chmod +x /start.sh
COPY ./start_mopidy.sh /
RUN chmod +x /start_mopidy.sh

COPY ./start.py /
RUN chmod +x /start.py
STOPSIGNAL SIGINT

COPY ./templates /home/templates

COPY ./templates/mopidy.conf /config/mopidy.conf
COPY ./env_vars.sh /
RUN chmod +x /env_vars.sh
RUN bash /env_vars.sh >> /etc/environment

COPY ./scan_library.sh /
RUN chmod +x /scan_library.sh


# Allows any user to run mopidy, but runs by default as a randomly generated UID/GID.
RUN set -ex \
 && usermod -G audio,sudo mopidy \
 && chown mopidy:audio -R /home /start.sh \
 && chmod go+rwx -R /home /start.sh

RUN echo "MOPIDY IRIS NEEDS THIS" >> /IS_CONTAINER
RUN apt-get install -y dbus && apt-get clean
RUN export DBUS_SESSION_BUS_ADDRESS=unix:path=/host/run/dbus/system_bus_socket

ENTRYPOINT [ "/start.sh" ]