Revisión de la máquina de volumen: server_process.py, sección 'if (change_gain or change_eq):'

1) La ganancia requerida por la curva EQ
eq_gain  = max(eq_mag) se inicializaba a cero al inicio de server process, pero es innecesario. De hecho la he quitado como variable general, se trabaja directamente con max(eq_mag) después de pintar la curva de EQ, se usa par
a evaluar el headroom.

2) gmax = 0    # tope de ganancia que admitimos en Brutefir.
Nueva variable en audio/config, normalmente es cero (se podría quere bajar).

3) Se quitan las evaluaciones intermedias al tratar level y gain. Se delega en la fase de control de headroom que
 hacemos después de conocer la curva EQ requerida.

4) Se deja de escribir el archivo lspk/altavoz/speaker en caso de pruebas de "quita y pon" systemEQ. El eventual estado de system_eq se refleja en el archivo de estado. Al arranque del server con do('syseq') se cargará la configuración systemEQ del archivo lspk/altavoz/speaker.

6) "maxlevel" se reduce a un valor informativo en el ámbito de do() y se renombra a "maxlevel_i". Sirve para hacer un potenciómetro de volumen, por ejemplo el slider de la página web. Afecta a www/js/functions.js y al pdf de comandos del server.

Resumen del nuevo código de la máquina de volumen:

    if (change_gain or change_eq):

        # Info para un potenciómetro de volumen (p.ej. el slider de la web)
        maxlevel_i = gmax - ref_level_gain - input_gain

        # 1a) Si se pide cambio de level (vol. calibrado)
        if not gain_direct:
            gain = level + ref_level_gain + input_gain  # se traduce a gain.
        # 1b) o se pide un cambio de ganacia en bruto.
        else:
            level = gain - ref_level_gain - input_gain

        # 2) Confección de la CURVA de EQ: Loudness + SysEQ (+RoomGain -HouseCurve) + Bass + Treble.
        se mira si se usa la phase
        inicialización a zeros

        if loudness_track:
        ... ...
        if system_eq:
        ... ...
        if treble != 0:
        ... ...
        if bass != 0:
        ... ...

        # 3) Calculamos el HEADROOM:
        headroom = gmax - gain - max(eq_mag)

        # 4) Priorizamos SysEQ bajando el level si NO hubiera HEADROOM:
        if 'syseq' in command and headroom < 0:
            gain  -= ceil(-headroom)
            level -= ceil(-headroom)
            headroom = gmax - gain - max(eq_mag)    # recalculamos el headroom

        # 5) SI hay HEADROOM suficiente aplicamos los cambios de level y/o EQ:
        if headroom >= 0:
            if change_gain:
                ... 'cfia' (etapa input de brutefir)
            if change_eq:
                ... 'lmc eq' (eq de Brutefir)

        # Si NO hay HEADROOM, no aplicamos los cambios, y recuperamos los valores anteriores
        else:
            warnings.append("Not enough headroom")
            recuperamos "valores_old"
