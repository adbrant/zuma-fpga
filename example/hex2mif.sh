#!/bin/sh
cat $1 | cut -c 12-21 | grep ^00 | cut -c 3-10
