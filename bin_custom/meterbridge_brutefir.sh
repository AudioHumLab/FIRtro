#!/bin/bash

killall meterbridge
meterbridge -n meter_brutefir -t dpm brutefir:input-0 brutefir:input-1 &

