#!/bin/bash

killall ecasound
sleep .2

# Para medir un driver al aire que radía en dipolo:
# aplicamos compensación de dipolo low pass 6 dB/oct
# podemos limitar el alcance modificando FREQ

FREQ=100

ecasound -i jack -o jack,system -el:lpf,$FREQ &
sleep .2

jack_connect ecasound:out_1 zita-Device-OUT:playback_3
jack_connect ecasound:out_2 zita-Device-OUT:playback_4


