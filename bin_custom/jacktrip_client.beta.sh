#!/bin/bash

servidor=192.168.1.138

killall jacktrip
killall -9 meterbridge
sleep 1

jacktrip -c $servidor &
sleep 1

jack_disconnect JackTrip:receive_1 system:playback_1
jack_disconnect JackTrip:receive_2 system:playback_2

jack_connect JackTrip:receive_1 brutefir:input-0
jack_connect JackTrip:receive_2 brutefir:input-1

sleep .5

meterbridge -t dpm -n meterbridge brutefir:input-0 brutefir:input-1 &

