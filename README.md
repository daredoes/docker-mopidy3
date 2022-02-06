This container packages [mopidy3](https://mopidy.com)

Comes pre-loaded with spotify, youtube, gstreamer, iris, etc

Built on Ubuntu.

Made because the only other option wasn't working for me :(

### Examples

Broadcast audio from /tmp/pcm-pipe:

    docker run -d \
        -v /tmp/pcm-pipe:/data/snapfifo \
        -p 1704:1704 \
        -p 1705:1705 \
        daredoes/mopidy3

### Config