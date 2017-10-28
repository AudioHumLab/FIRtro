#!/bin/bash

# Script auxiliar para ser ejecutado por el php de la página web

# (i) Los comandos a Spotify solo funcionan si coinciden tanto
#     el usuario como la sesión que corren FIRtro y Spotify.

playerctl --player=spotify $*
