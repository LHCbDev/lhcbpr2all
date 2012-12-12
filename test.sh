#!/bin/sh

cd $(dirname $0)

nosetests -v --with-doctest --with-coverage --cover-erase --cover-inclusive --cover-package LHCbNightlies2 python
