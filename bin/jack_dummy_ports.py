#!/usr/bin/python
# -*- coding: utf-8 -*-
""" v1.0a
    Crea los puertos dummy declarados en audio/config
    que podrán ser usados por las fuentes encendidas 
    pero no seleccionadas por el selector de entradas.
"""
# https://pypi.python.org/pypi/py-jack/0.5.2
import jack
from getconfig import dummy_ports
dummy_ports = dummy_ports.split() # vienen separados por espacios

jackdummy = jack.Client("dummy")

for puerto in dummy_ports:
    p = puerto.split(":")[-1]
    # jackdummy.register_port(p, 1) o bien podemos usar la siguiente sintaxis
    #                               para crear un puerto escribible:
    jackdummy.register_port(p, jack.IsInput)

jackdummy.activate()
