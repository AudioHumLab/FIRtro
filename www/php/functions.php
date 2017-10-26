<?php
    $config_file = "../config/config.ini";
    $config;
    $config_ws;
    $fifoCddaPath = "/home/firtro/cdda_fifo";
    $fifoTdtPath = "/home/firtro/tdt_fifo";
    $command = $_REQUEST["command"];
    $value = $_REQUEST["value"];
    $json = null;

    function firtro_socket ($data) {
        $service_port = 9999;
        $address = "127.0.0.1";

        /* Crear un socket TCP/IP. */
        $socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
        if ($socket === false) {
            echo "socket_create() falló: razón: " . socket_strerror(socket_last_error()) . "\n";
        }

        $result = socket_connect($socket, $address, $service_port);
        if ($result === false) {
            echo "socket_connect() falló.\nRazón: ($result) " . socket_strerror(socket_last_error($socket)) . "\n";
        }

        socket_write($socket, $data, strlen($data));
        $out = socket_read($socket, 4096);
        socket_write($socket, "close", strlen("close"));
        socket_read($socket, 4096);
        socket_close($socket);
        return $out;
    }
    
    function fifo_write($fifoPath, $data) {
        $fifo_w = fopen($fifoPath, 'w'); 
        fwrite ($fifo_w, $data . "\n");
        #fclose ($fifo_w);
        fflush ($fifo_w);
        sleep(1);
    }
    
    // Funcion para escribir el fichero de configuracion. Las funciones standard de PHP no lo incluyen
    function write_ini_file($assoc_arr, $path, $has_sections=FALSE) { 
        $content = ""; 
        if ($has_sections) { 
            foreach ($assoc_arr as $key=>$elem) { 
                $content .= "[".$key."]\n"; 
                foreach ($elem as $key2=>$elem2) { 
                    if(is_array($elem2)) 
                    { 
                        for($i=0;$i<count($elem2);$i++) 
                        { 
                            $content .= $key2."[] = \"".$elem2[$i]."\"\n"; 
                        } 
                    } 
                    else if($elem2=="") $content .= $key2." = \n"; 
                    else $content .= $key2." = \"".$elem2."\"\n"; 
                } 
            } 
        } 
        else { 
            foreach ($assoc_arr as $key=>$elem) { 
                if(is_array($elem)) 
                { 
                    for($i=0;$i<count($elem);$i++) 
                    { 
                        $content .= $key2."[] = \"".$elem[$i]."\"\n"; 
                    } 
                } 
                else if($elem=="") $content .= $key2." = \n"; 
                else $content .= $key2." = \"".$elem."\"\n"; 
            } 
        } 

        if (!$handle = fopen($path, 'w')) { 
            return false; 
        } 
        if (!fwrite($handle, $content)) { 
            return false; 
        } 
        fclose($handle); 
        return true; 
    }

    if($command == 'level_up') {
        $json=firtro_socket ("level_add 1");
        }
    elseif($command == 'level_up_3') {
        $json=firtro_socket ("level_add 3");
        }
    elseif($command == 'level_down') {
        $json=firtro_socket ("level_add -1");
        }
    elseif($command == 'level_down_3') {
        $json=firtro_socket ("level_add -3");
        }
    elseif($command == 'vol_slider') {
        $json=firtro_socket ("level $value");
        }
    elseif($command == 'bal_slider') {
        $json=firtro_socket ("balance $value");
        }
    elseif($command == 'mute') {
        $json=firtro_socket ("toggle");
        }
    elseif($command == 'mono') {
        $json=firtro_socket ("mono toggle");
        }
    elseif($command == 'status') {
        $json=firtro_socket ("status");
        }
    elseif($command == 'loudness_switch') {
        if ($value == "on") $json=firtro_socket ("loudness_track");
        else $json=firtro_socket ("loudness_track_off");
        }
    elseif($command == 'loudness_toggle') {
        $fstatusRaw = firtro_socket("status");
        $firtro_status = json_decode($fstatusRaw);
        $loudness_track = $firtro_status->{"loudness_track"};
        if ($loudness_track)         $json=firtro_socket("loudness_track_off");
        else                         $json=firtro_socket("loudness_track");
        }
    elseif($command == 'loud_ref_down') {
        $json=firtro_socket ("loudness_add -1");
        }
    elseif($command == 'loud_ref_up') {
        $json=firtro_socket ("loudness_add 1");
        }
    elseif($command == 'loudness_slider') {
        $json=firtro_socket ("loudness_ref $value");
        }
    elseif($command == 'loud_ref_reset') {
        $json=firtro_socket ("loudness_ref 0");
        }
    elseif($command == 'syseq_switch') {
        if ($value == "on") $json=firtro_socket ("syseq");
        else $json=firtro_socket ("syseq_off");
        }
    elseif($command == 'peq_switch') {
        if ($value == "on") $json=firtro_socket ("peq_reload");
        else $json=firtro_socket ("peq_defeat");
        }
    elseif(substr($command,0,3) == 'drc') {
        $value=substr($command, -1);
        $json=firtro_socket ("drc $value");
        }
    elseif($command == 'bass_up') {
        $json=firtro_socket ("bass_add 1");
        }
    elseif($command == 'bass_down') {
        $json=firtro_socket ("bass_add -1");
        }
    elseif($command == 'treble_up') {
        $json=firtro_socket ("treble_add 1");
        }
    elseif($command == 'treble_down') {
        $json=firtro_socket ("treble_add -1");
        }        
    elseif($command == 'eq_flat') {
        $json=firtro_socket ("flat");
        }
    elseif($command == 'input_select') {
        $json=firtro_socket ("input $value");
        }
    elseif($command == 'preset_select') {
        $json=firtro_socket ("preset $value");
        }
    elseif(substr($command,0,6) == 'keypad') {
        # Estraemos el numero, que va en ultima posición (0-9)
        # $number = substr($command,-1);
        # Cambio la funcion por si el dia de mañana se quieren poner valores >9
        $config = parse_ini_file($config_file);
        $number = substr($command,7);
        switch ($value) {
            case 'mpd':
            case $config['mpd_input']:
                shell_exec("/usr/bin/mpc play $number");
                break;
            case 'cdda':
            case $config['cdda_input']:
                $number = $number-1;
                $json=fifo_write ($fifoCddaPath, "seek_chapter $number 1");
                break;
            case 'tdt':
            case $config['tdt_input']:
                shell_exec ("/home/firtro/bin/radio_channel.py $number");
                $json=firtro_socket ("status");
                break;
            default:
                $json=firtro_socket ("status");
                break;
        }
                $json=firtro_socket ("status");
    }
    elseif($command == 'play') {
        $config=parse_ini_file($config_file);
        switch ($value) {
            case 'mpd':
            case $config['mpd_input']:
                shell_exec("/usr/bin/mpc play");
                break;
            case 'cdda':
            case $config['cdda_input']:
                fifo_write ($fifoCddaPath, "loadfile cdda://");
                break;
            case 'tdt':
            case $config['tdt_input']:
                shell_exec("/usr/local/bin/canal -c");
                break;
            default:
                break;
        }
        $json=firtro_socket ("status");
    }
    elseif($command == 'pause') {
        $config=parse_ini_file($config_file);
        switch ($value) {
            case 'mpd':
            case $config['mpd_input']:
                shell_exec("/usr/bin/mpc toggle");
                break;
            case 'cdda':
            case $config['cdda_input']:
                fifo_write ($fifoCddaPath, "pause");
                break;
            case 'tdt':
            case $config['tdt_input']:
                break;
            default:
                break;
        }
        $json=firtro_socket ("status");
    }
    elseif($command == 'stop') {
        $config=parse_ini_file($config_file);
        switch ($value) {
            case 'mpd':
            case $config['mpd_input']:
                shell_exec("/usr/bin/mpc stop");
                break;
            case 'cdda':
            case $config['cdda_input']:
                fifo_write ($fifoCddaPath, "stop");
                break;
            case 'tdt':
            case $config['tdt_input']:
                fifo_write ($fifoTdtPath, "stop");
                break;
            default:
                break;
        }
        $json=firtro_socket ("status");
    }
    elseif($command == 'prev') {
        $config=parse_ini_file($config_file);
        switch ($value) {
            case 'mpd':
            case $config['mpd_input']:
                shell_exec("/usr/bin/mpc prev");
                break;
            case 'cdda':
            case $config['cdda_input']:
                fifo_write ($fifoCddaPath, "seek_chapter -1");
                break;
            case 'tdt':
            case $config['tdt_input']:
                break;
            default:
                break;
        }
        $json=firtro_socket ("status");
    }
    elseif($command == 'next') {
        $config=parse_ini_file($config_file);
        switch ($value) {
            case 'mpd':
            case $config['mpd_input']:
                shell_exec("/usr/bin/mpc next");
                break;
            case 'cdda':
            case $config['cdda_input']:
                fifo_write ($fifoCddaPath, "seek_chapter 1");
                break;
            case 'tdt':
            case $config['tdt_input']:
                break;
            default:
                break;
        }
        $json=firtro_socket ("status");
    }
    elseif($command == 'ff') {
        $config=parse_ini_file($config_file);
        switch ($value) {
            case 'mpd':
            case $config['mpd_input']:
                shell_exec("/usr/bin/mpc seek +00:00:10");
                break;
            case 'cdda':
            case $config['cdda_input']:
                fifo_write ($fifoCddaPath, "seek +10");
                break;
            case 'tdt':
            case $config['tdt_input']:
                break;
            default:
                break;
        }
        $json=firtro_socket ("status");
    }
    elseif($command == 'rw') {
        $config=parse_ini_file($config_file);
        switch ($value) {
            case 'mpd':
            case $config['mpd_input']:
                shell_exec("/usr/bin/mpc seek -00:00:10");
                break;
            case 'cdda':
            case $config['cdda_input']:
                fifo_write ($fifoCddaPath, "seek -10");
                break;
            case 'tdt':
            case $config['tdt_input']:
                break;
            default:
                break;
        }
        $json=firtro_socket ("status");
    }
    elseif($command == 'eject') {
        $config=parse_ini_file($config_file);
        switch ($value) {
            case 'mpd':
            case $config['mpd_input']:
                shell_exec("/usr/bin/mpc stop");
                break;
            case 'cdda':
            case $config['cdda_input']:
                fifo_write ($fifoCddaPath, "stop");
                break;
            case 'tdt':
            case $config['tdt_input']:
                break;
            default:
                break;
        }
        shell_exec("sleep 1 && eject");
        $json=firtro_socket ("status");
    }
    elseif($command == 'cd-mpd') {
    $json=firtro_socket ("exec mcd.py");
    }
    elseif($command == 'media-mpd') {
    $json=firtro_socket ("exec media.py");
    }
    elseif($command == 'eject-usb') {
    $json=firtro_socket ("exec media.py eject");
    }
    elseif($command == 'eject-cd') {
    shell_exec("sleep 1 && eject");
    $json=firtro_socket ("status");
    }
        
    elseif(substr($command,0,7) == 'custom_') {
        $config=parse_ini_file($config_file);
        #$tmp1 = 'val_custom_'.substr($command,7);
        # Con una doble variable se puede evaluar el texto que contiene tmp1 como una variable
        #$custom_value = $$tmp1;
        $custom_value = $config["btn_cmd_".substr($command,7)];
        if ($custom_value <> "") $json=firtro_socket ("exec $custom_value");
        else $json=firtro_socket ("status");
    }
    elseif($command == 'save_config') {
        $config_ws=parse_ini_file($config_file,true);
        # $value solo contiene los valores que han cambiado
        # Recorremos el array de configuraciones para compararlos con los cambios
        foreach ($config_ws as $key=>$elem) { # Nivel 1 (secciones)
            foreach ($elem as $key2=>$elem2) { # Nivel 2 (opciones)
                foreach ($value as $key3=>$elem3) { # Recorremos el array de cambios
                    if ($key2 == $key3) $config_ws[$key][$key2]=$elem3; # Si alguna opcion coincide, la actualizamos con el nuevo valor
                }
            }
        }
        write_ini_file($config_ws, $config_file, true);
        $json=firtro_socket ("status");
    }
 echo $json;
?>
