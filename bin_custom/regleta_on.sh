#!/bin/bash

# Aqui esta el CD
sispmctl -o 1
sleep 2

# Aqui esta el convertidor coax/opt M-Audio CO2
sispmctl -o 2
sleep .5

# El sinto
sispmctl -o 3
sleep .5

# Aqui está la regleta de los amplis, previo, DEQ, y la regleta color crema: plato y phono
sispmctl -o 4
sleep 2

