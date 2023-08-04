#!/bin/bash
. env
if [ ! -z "$1" ] ; then
	VERSION=$1
fi
echo "VERSION=$VERSION"
echo "USERNAME=$USERNAME"
echo "IMAGE_NAME=$IMAGE_NAME"

set -ex

if [[ "$1" == "--no-cache" ]] ; then
	echo "########### Fresh no-cache build ###########"
	docker build --no-cache --rm -t $USERNAME/$IMAGE_NAME:latest .
else
	echo "########### Building using build-cache ###########"
	docker build -t $USERNAME/$IMAGE_NAME:latest .
fi

chmod 755 ReEncrypt