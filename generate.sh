#!/bin/bash

set -e

function create_ribs {
    python create-ribs.py --prefixes unique-prefixes.txt \
	--topo inet-edges.txt \
	--dir inet \
	--log \
	--routes routes \
	--rib inet-ribs.csv
}

function fetch_bgpdump {
    url='http://irl.cs.ucla.edu/bgpparser/download.cgi?file=bgpparser-0.3b2.tgz'

    if [ -f bgpparser/bin/bgpparser ] && [ ! bgpparser/bin/bgpparser ]; then
	return
    fi

    if [ ! -f bgpparser.tgz ]; then
	wget $url -O bgpparser.tgz
    fi

    tar xf bgpparser.tgz
    pushd bgpparser
    ./configure
    pushd parser
    # This only works on Linux.  Not sure what the workaround on Mac
    # OSX systems is.
    sed -i.bak 's/^CFLAGS=.*/CFLAGS=-g -fPIC -fpermissive/g' Makefile
    popd
    make
    popd
}

function get_prefixes {
    RIBFILE=rib.20130801.0000
    if [ ! -f $RIBFILE ]; then
	echo "Please download RIB file in MRT format from http://routeviews.org/bgpdata/2013.08/RIBS/"
	exit
    fi

    bgpparser/bin/bgpparser -f $RIBFILE |  \
	grep PREFIX |  \
	sed -e 's/PREFIX//g' -e 's/<//g' -e 's|/>||g' -e 's/>//g' |  \
	awk '{ print $1 }' | uniq | unique-prefixes.txt
}

fetch_bgpdump
if [ ! -f unique-prefixes.txt ]; then
    get_prefixes
fi

create_ribs
