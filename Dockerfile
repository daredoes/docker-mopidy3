FROM ubuntu:20.04

EXPOSE 5555 6600 6680 9001

# Order based on how to effectively cache docker image
RUN apt-get update
# tzdata has an interactive prompt that doesn't play nicely with docker when its a dependency
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata
RUN apt-get install -y cron lsof supervisor wget git gnupg python3 python3-pip pkg-config libffi-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev libcairo2-dev libgirepository1.0-dev build-essential libasound2-dev && apt-get clean
# Stuff for youtube videos
RUN apt-get install -y libmpg123-dev libmp3lame-dev gstreamer1.0-tools gstreamer1.0-alsa gstreamer1.0-libav gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly && apt-get clean
# Needed for ubuntu-advantage-tools EULA
RUN echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true | debconf-set-selections

RUN wget -q -O - https://apt.mopidy.com/mopidy.gpg | apt-key add -
RUN wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/buster.list

RUN apt-get update --allow-insecure-repositories
RUN apt-get -y upgrade
RUN apt-get install -y --allow-unauthenticated mopidy mopidy-local mopidy-mpd
RUN apt-get install -y --fix-missing ubuntu-restricted-extras

RUN python3 -m pip install pycairo

RUN mkdir -p /var/log/supervisor

COPY ./templates/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY ./templates/system.sh /home/system.sh

# An empty line is required at the end of this file for a valid cron file.

COPY ./requirements.txt /
RUN python3 -m pip install -r /requirements.txt
RUN export IRIS_DIR=$(pip3 show mopidy_iris | grep Location: | sed 's/^.\{10\}//') && echo "mopidy ALL=(ALL) NOPASSWD: $IRIS_DIR/mopidy_iris/system.sh" >> /etc/sudoers && chmod -R 755 $IRIS_DIR/mopidy_iris/ && chmod -R 755 /root/ && chmod -R 755 /root/.cache/ && sed -i 's/_USE_SUDO = True/_USE_SUDO = False/g' $IRIS_DIR/mopidy_iris/system.py

COPY ./start.sh /
RUN chmod +x /start.sh
COPY ./start_mopidy.sh /
RUN chmod +x /start_mopidy.sh

COPY ./start.py /
RUN chmod +x /start.py
STOPSIGNAL SIGINT

COPY ./templates /home/templates

COPY ./templates/mopidy.conf /etc/mopidy/mopidy.conf

COPY ./scan_library.sh /
RUN chmod +x /scan_library.sh

# Allows any user to run mopidy, but runs by default as a randomly generated UID/GID.
RUN set -ex \
 && usermod -G audio,sudo mopidy \
 && chown mopidy:audio -R /home /start.sh \
 && chmod go+rwx -R /home /start.sh

RUN echo "MOPIDY IRIS NEEDS THIS" >> /IS_CONTAINER
RUN mkdir /home/cache

# Add crontab file in the cron directory
COPY ./cronjob /etc/cron.d/cronjob

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/cronjob

# Apply cron job
RUN crontab /etc/cron.d/cronjob

ENV XDG_CACHE_DIR="/cache"
ENV XDG_CONFIG_DIR="/etc/mopidy"
ENV XDG_DATA_DIR="/data"
ENV REQUIREMENTS_FILE="/etc/mopidy/requirements.txt"
ENV IRIS_USE_SUDO=false
ENV TEMPLATES_DIR="/home/templates"
ENV LOCAL_SCAN_INTERVAL="300"

COPY ./requirements.txt /etc/mopidy/requirements.txt
COPY ./templates/servers.json /etc/mopidy/servers.json
COPY ./web.py /
COPY ./tailwind.js /
RUN chmod +x /tailwind.js
RUN chmod +x /web.py

ENTRYPOINT [ "/start.sh" ]