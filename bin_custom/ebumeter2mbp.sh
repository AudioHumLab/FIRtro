#!/bin/bash

display_prev=$DISPLAY

export DISPLAY="192.168.1.140:0"

/home/rafax/bin2/ebumeter.py

export DISPLAY=$display_prev

exit 0
