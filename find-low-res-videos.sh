#!/bin/bash
# finds non-HD videos in your collection
# requires get-streams.sh

EMR="\033[1;31m"
EMY="\033[1;33m"
NONE="\033[0m"

if [ $? -gt 0 ]; then
    videosdir="$@"
else
    videosdir_config="$(sed -n 's/VideosDir\s*[=:]\s*\([\/A-Za-z0-9\.\_\-].*\)/\1/p' mythtv.conf)"
    if [[ ! -z "${videosdir_config// }" ]]; then
        videosdir="$videosdir_config"
    else
        echo "Please specify videos directory"
        exit 1
    fi
fi

for i in $videosdir/*.{avi,mp4,mkv,iso,mpeg,flv,m4v,mpg,m2ts}; do
    RES="$(sh get-streams.sh "${i}" | egrep 'Video.*[0-9]{3,4}x[0-9]{3,4}' | sed 's/.*\( .*x[0-9]*[ ,]\).*/\1/g' | sed 's/\,//g' | head -n 1)"
    WIDTH="$(echo $RES | cut -dx -f1)"
    HEIGHT="$(echo $RES | cut -dx -f2)"
    if [ "$HEIGHT" -lt 640 ]; then
        COLOR=$NONE
        [ "$HEIGHT" -lt 480 ] && COLOR=$EMY
        [ "$HEIGHT" -lt 320 ] && COLOR=$EMR
        echo -e "${COLOR}${RES}\t${i}${NONE}"
    fi
done
