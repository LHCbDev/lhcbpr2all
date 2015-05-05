#!/bin/bash

for i in $(dirname $0)/utils.d/*.sh ; do
    . "$i"
done