#!/bin/bash

# script used in firtro's crontab

/home/firtro/bin_custom/reles.py 2 on
/home/firtro/bin/control level -24
mpc clear; mpc load despertador; mpc random on; mpc play
