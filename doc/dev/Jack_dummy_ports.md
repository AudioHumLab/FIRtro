**NOTA:** viene de la issue#11

**@rripio**

> Hace tiempo pensaba en este problema de las conexiones automáticas al encenderse mplayer y mpd, y se me ocurrió (y no escribí) que deberían conectarse a unos puertos "dummy".
> Miré en su día cómo implementar un cliente dummy y me desanimé: no caí, y caigo ahora, que lo obvio es hacer dos entradas "sumidero" en brutefir (o eca, para el caso) que no vayan a ninguna parte. A partir de ahí todo es negocio del selector de entradas.

**@amiguelez**

> Me parece muy buena idea esa Roberto.

## Solución propuesta:
Puertos dummy en jack directamente en lugar de en brutefir/ecasound.

**bin/jack_dummy_ports.py**

      # https://pypi.python.org/pypi/py-jack/0.5.2
      import jack
      from getconfig import dummy_ports
      dummy_ports = dummy_ports.split() # vienen separados por espacios
      jackdummy = jack.Client("dummy")
      for puerto in dummy_ports:
          p = puerto.split(":")[-1]
          jackdummy.register_port(p, jack.IsInput) # se crea un puerto escribible
      jackdummy.activate()

**audio/config** y **bin/getconfig.py**

    [misc]
    ; -- Declaracion de puertos dummy:
    dummy_ports: dummy:null_0 dummy:null_1

**bin/mpdconf_adjust.py**

Nueva opción "dummy" disponible en la función `modifica_jack_destination_ports(opcion)`

**bin/initfirtro.py**

Se mantiene la verificación de que los puertos jack a los que apunta .mpdconf sean los correctos (ahora 'dummy').

**.mpdconf**

`initfirtro.py` se ocupa de que `destination_ports` apunte a dummy en jack.

**.mplayer/config**

Se mantiene la configuración ´ao=jack:name=mplayer_xx:noconnect´ al objeto de evitar que "la radio esté encendida" cuando se haga "input restore" en el arranque del sistema (initfirtro.py).

**server_process.py**

 Levanta los nuevos puertos dummy en jack con `import jack_dummy_ports`
 
 
