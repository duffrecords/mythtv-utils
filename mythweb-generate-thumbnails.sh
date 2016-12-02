#!/bin/bash

# Generate all the missing video thumbnails so MythWeb doesn't show
# a bunch of broken links.

# requires mogrify installed

# user-defined variables
ARTWORK_DIR="$(python get_backend_config.py CoverartDir)"
USER_GROUP="$(stat -c '%U:%G' $ARTWORK_DIR)"
exit

if ! which mogrify 2>&1 > /dev/null; then
    echo "Error: ImageMagick not installed!"
    exit 1
fi

mkdir -p ${ARTWORK_DIR}/thumbnails
chown ${USER_GROUP} ${ARTWORK_DIR}/thumbnails
chmod g+w ${ARTWORK_DIR}/thumbnails

cd ${ARTWORK_DIR}
for i in *.jpg; do
	if [[ ! -f "thumbnails/$i" ]]; then
		/usr/bin/mogrify -format jpg -path thumbnails -thumbnail 94x140 "$i"
		chown ${USER_GROUP} "thumbnails/$i"
		chmod g+w "thumbnails/$i"
	fi
done
