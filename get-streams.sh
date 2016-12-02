#!/bin/bash
# prints stream data from media files, with highlighting
# requires ffmpeg installed

FFMPEG="$(which ffmpeg || which mythffmpeg || echo 'Error: ffmpeg not installed!' && exit 1)"

if [ $# -ne 1 ]; then
  echo "Usage: $0 file"
  exit 1
fi

$FFMPEG -i "$@" 2>&1 | egrep 'Stream|Duration' | egrep --color 'stereo|5\.1|7\.1|bitrate: [0-9]* kb\/s|aac|ac3|dts|mp3|mp2|vorbis|truehd|h264|mpeg2video|mpeg4|hevc|msmpeg4v3| [0-9]{3,4}x[0-9]{3,4}|([0-9\.]*) fps|Subtitle|eng|$'
