#!/bin/sh

echo Building configuration system...
autoreconf -i
if [ $? -ne 0 ]; then
	exit 1
fi
rm -rf autom4te.cache
echo Now run ./configure

