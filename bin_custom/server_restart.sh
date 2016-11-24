#!/bin/bash

pkill -f server.py
sleep .5
/home/firtro/bin/server.py &
