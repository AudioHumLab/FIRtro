#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Modulo interno para acomodar el FIRtro con Pulseadio
"""
import subprocess as sp

class Tarjeta_pa:
    def __init__(self, numero, nombre, modulo_alsa):
        self.numero = numero
        self.nombre = nombre
        self.modulo_alsa = modulo_alsa

def release_all_cards():
    ''' para que Pulseaudio deje libres todas las tarjetas del sistema.
    '''
    tarjetas = []

    # leemos la lista de tarjetas de pulseadio
    printado = sp.check_output("pactl list short cards", shell=True)
    for linea in printado.split("\n"):
        if linea: # eludimos tratar lineas vacias (la última línea del printado está vacía)
            # el printado de tarjetas viene tabulado en tres campos:
            #      numTarjeta   nombreTarjeta    moduloAlsa
            # guardamos la tarjeta con sus tres campos
            tarjetas.append(Tarjeta_pa(linea.split()[0], linea.split()[1], linea.split()[2]))

    for tarjeta in tarjetas:
        comando = "pactl set-card-profile " + tarjeta.nombre + " off"
        tmp = sp.check_output(comando, shell=True)
        if tmp: # algo ha ido mal
            print "(pulse_manager):"
            print tmp
        else:   # comando aceptado
            print "(pulse_manager) se desactiva la tarjeta en PA: " + tarjeta.nombre

def pulse_detected():
    """ comprueba si pulseaudio está corriendo
    """
    pa = sp.check_output("pgrep -fl pulseaudio", shell=True)
    if "pulseaudio" in pa:
        return True
    else:
        return False

def rtp_receiver():
    """ cargamos el módulo de recepción RTP
    """
    tmp = "pactl load-module module-rtp-recv"
    sp.call(tmp, shell = True)

    #   NOTA: resampling en el módulo RTP RECEIVER
    #   Pulseaudio resampleará lo que llegue por streaming RTP.
    #   -Pulseaudio corre por cuenta de la sesión de escritorio-
    #   Podemos especificar la calidad de resampling en el archivo
    #   ~/.pulse/daemon.conf
    #       default-sample-rate = 44100
    #       resample-method = src-sinc-best-quality
    #   Podremos comprobar el módulo module-rtp-recv con el comando
    #   $ pactl list modules
    #   OjO: Pulseaudio 5.0 CREO que dispone de otros resamplers de interés como es SOX.

def pulse2jack():
    """ cargamos el módulo jack-sink
    """
    tmp = "pactl load-module module-jack-sink channels=2 client_name=pulse_sink connect=False"
    sp.call(tmp, shell = True)
    # Lo establecemos como salida por defecto de PA
    tmp = "pacmd set-default-sink jack_out"
    sp.call(tmp, shell = True)
    # Aseguramos volumen 100%
    tmp = "pactl set-sink-volume jack_out 100%"
    sp.call(tmp, shell = True)

if __name__ == '__main__':
    print __doc__
