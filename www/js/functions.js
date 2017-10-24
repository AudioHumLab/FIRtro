/////////////////////////////////////////
////////////*** VARIABLES ***////////////
/////////////////////////////////////////

// Direccion del script php en el server
var $php_url = "php/functions.php";
// Datos en bruto que retorna el servidor
var $php_data_raw;
// Variables procesadas que retorna el servidor
var $php_data;
// Array de datos de los gaficos
var $syseq_r_plot_data=[''];
var $syseq_l_plot_data=[''];
var $tone_plot_data=[''];
var $loudeq_plot_data=[''];
var $plot_data_new=[''];
// Objeto para guardar temporalmente los cambios realizados en la configuracion mientras no son salvados o descartados
var $config_changes={};
// Timeout de espera (ms) para hacer un resize de los gráficos cuando el tamaño de ventana cambia
var $resize_timeout=200;
// Valor del conjunto de pulsaciones del teclado numerico
var $keypad_value="";

// Opciones para el grafico (comun para todos)
$plot_options = {
    title: {
        text: '',   // title for the plot,
        show: false,
        fontSize:'9pt'
    },
    seriesDefaults: {
        rendererOptions: {
            //////
            // Turn on line smoothing.  By default, a constrained cubic spline
            // interpolation algorithm is used which will not overshoot or
            // undershoot any data points.
            //////
            smooth: true
        }
    },
    animate : false,
    axes: {
        xaxis: {
            pad: 0,
            ticks: ['20',[30,''],[40,''],[50,''],[60,''],[70,''],[80,''],[90,''],
                    '100',[200,''],[300,''],[400,''],[500,''],[600,''],[700,''],[800,''],[900,''],
                    [1000,'1K'],[2000,''],[3000,''],[4000,''],[5000,''],[6000,''],[7000,''],[8000,''],[9000,''],
                    [10000,'10K'],[11000,''],[12000,''],[13000,''],[14000,''],[15000,''],[16000,''],[17000,''],[18000,''],[19000,''],
                    [20000,'20K']],
            tickOptions:{fontSize:'8pt'},
            renderer: $.jqplot.LogAxisRenderer
        },
        yaxis: {
            pad: 0.5,
            //min: -6,
            //max: 6,
            ticks: ['-8','-6','-4','-2',[0,'0 dB'],'2','4','6','8'],
            tickOptions:{fontSize:'8pt'}
        }
    },
    series:[
        {
            lineWidth:2, 
            showMarker: false
        }
    ],
    canvasOverlay: {
      show: true,
      objects: [
        {dashedHorizontalLine: {
          name: '',
          y: 0,
          lineWidth: 1,
          color: 'rgb(100, 55, 124)',
          shadow: true,
          xOffset: 0,
          xmin:20,
          xmax:20000
        }}
      ]
  }
}

// Personalizamos las opciones para el grafico drc. Ojo, que los objetos no se pueden copiar igualándolos.
$plot_options_drc = jQuery.extend(true, {}, $plot_options);
// llegamos a +6dB para poder dibujar RoomGain positivos.
$plot_options_drc.axes.yaxis.ticks=['-16','-14','-12','-10','-8','-6','-4','-2',[0,'0 dB'],'2','4','6'];

/////////////////////////////////////////
////////////*** FUNCIONES ***////////////
/////////////////////////////////////////

// Esta es para poner en mayusculas y quitar los guiones bajos de las opciones leidas del fichero de configuracion
function capitalize(text) {
    array = [];
    text=text.replace("_", " ");
    text.split(" ").forEach(function(value) {
        array.push(value.substr(0, 1).toUpperCase() + value.substr(1).toLowerCase());
    });
    return array.join(" ");
}

// Restaura las opciones en caso de que se decida descartar los cambios
function restore_settings() {
    $.each ($config_changes, function(option, value) {
        if (option == 'global_theme') {
            $("#global_theme").val($config_ws['themes']['global_theme']).selectmenu('refresh', true);
            changeGlobalTheme($config_ws['themes']['global_theme']);
        }
        else $('#'+option).attr('value', $config[option]).text("refresh");
    });
    $config_changes={};
    console.log("Settings restored!");
}
// Collapse page navs after use
$(function(){
    $('body').delegate('.content-secondary .ui-collapsible-content', 'click',  function(){
        $(this).trigger("collapse");
    });
});

// jQuery no-double-tap-zoom plugin
// Triple-licensed: Public Domain, MIT and WTFPL license - share and enjoy!
// http://stackoverflow.com/questions/3103842/safari-ipad-prevent-zoom-on-double-tap
// https://gist.github.com/2047491

(function($) {
  var IS_IOS = /iphone|ipad/i.test(navigator.userAgent);
  $.fn.nodoubletapzoom = function() {
    if (IS_IOS)
      $(this).on('touchstart', function preventZoom(e) {
        var t2 = e.timeStamp
          , t1 = $(this).data('lastTouch') || t2
          , dt = t2 - t1
          , fingers = e.originalEvent.touches.length;
        $(this).data('lastTouch', t2);
        if (!dt || dt > 500 || fingers > 1) return; // not double-tap

        e.preventDefault(); // double tap - prevent the zoom
        // also synthesize click events we just swallowed up
        $(this).trigger('click').trigger('click');
      });
  };
})(jQuery);

// Función para enviar comandos al servidor
function send_command(command, value) {
    //console.log(command)
    $.ajax({
        type: "POST",
        url: $php_url,
        data: ({command: command, value: value}),
        cache: false,
        dataType: "text",
        success: onSuccess,
        error: onError
    });
}

// Funcion para actualizar periodicamente la página según el tiempo especificado
// Se vuelve a hacer una petición ajax independiente que la que se usa para actualizar en los cambios de página
// La razón es que de esta forma el tiempo de espera (window.setTimeout) se puede poner después de recibir los datos y actualizar la página, de forma síncrona
// Esto evita que se produzcan llamadas simultaneas ajax si éstas tardan mas que el tiempo de espera
function auto_update() {
    $.ajax({
        type: "POST",
        url: $php_url,
        data: ({command: "status", value: "0"}),
        cache: false,
        dataType: "text",
        success: function(data){
            onSuccess(data);
            window.setTimeout(auto_update, $config['auto_update_interval']);
        },
        error: function (XMLHttpRequest, textStatus, errorThrown){
            onError(XMLHttpRequest, textStatus, errorThrown);
            window.setTimeout(auto_update, $config['auto_update_interval']);
        }
    });
}

// Si el comando se envía correctamente, la respuesta se procesa aqui.
function onSuccess(data) {
    // Intentamos guardar los datos recibidos y capturamos la excepcion si ocurre un error
    try { eval( '$php_data_raw=' + data ); }
    catch(ex) {
        alert ("Error in server response. Type of data is "+typeof($php_data_raw)+".\nIs the FIRtro server running?");
        $php_data_raw = null;
        return;
    }
    // Comparamos el objeto recibido con el almacenado, y actualizamos solo si difieren
    if (JSON.stringify($php_data) !== JSON.stringify($php_data_raw)) {
        $php_data = $php_data_raw;
        // Prueba chapuzas para retrasar a voluntad la actualizacion de la pagina y comprobar que el auto update no envia otra petición hasta que termine
        //alert("Hola");
        //$force_update=0;
        update_controls ();
    }
}

// Si se produce un error, mostramos un mensaje con la causa del problema
function onError (request, status, error) {
    //alert("Failed to load resource: " + $php_url);
    console.log ("Failed to load resource: " + $php_url);
    console.log ("Request: " + request);
    console.log ("Status: " + status);
    console.log ("Error: " + error);
}

// Dynamically changes the theme of all UI elements on all pages,
// also pages not yet rendered (enhanced) by jQuery Mobile.
// http://stackoverflow.com/questions/7667603/change-data-theme-in-jquery-mobile
//$.mobile.changeGlobalTheme = function(theme)
function changeGlobalTheme(theme)
{
    // These themes will be cleared, add more
    // swatch letters as needed.
    // Esta variable la paso al config como $config['themes']
    //var themes = " a b c d e";

    // Updates the theme for all elements that match the
    // CSS selector with the specified theme class.
    function setTheme(cssSelector, themeClass, theme)
    {
        $(cssSelector)
            .removeClass($config['themes'].split(" ").join(" " + themeClass + "-"))
            .addClass(themeClass + "-" + theme)
            .attr("data-theme", theme);
    }

    // Add more selectors/theme classes as needed.
    setTheme(".ui-mobile-viewport", "ui-overlay", theme);
    setTheme("[data-role='page']", "ui-body", theme);
    setTheme("[data-role='header']", "ui-bar", theme);
    setTheme("[data-role='footer']", "ui-bar", theme);
    setTheme("[data-role='listview'] > li", "ui-bar", theme);
    setTheme(".ui-btn", "ui-btn-up", theme);
    //setTheme(".ui-btn", "ui-btn-down", theme);
    //setTheme(".ui-btn", "ui-btn-hover", theme);
};

// Left|right pad. Se usó abajo en case: "info_page", pero actualmente se usan los grid jquery.
// http://sajjadhossain.com/2008/10/31/javascript-string-trimming-and-padding/
String.prototype.lpad = function(padString, length) {
	var str = this;
    while (str.length < length)
        str = padString + str;
    return str;
}
String.prototype.rpad = function(padString, length) {
	var str = this;
    while (str.length < length)
        str = str + padString;
    return str;
}

// Actualización de los valores de la página
function update_controls () {
    $("[name='tittle']").text("FIRtro [" + $php_data["loudspeaker"] + "]");
    var $first_item=true;
    // Página activa del documento
    switch ($.mobile.activePage.attr('id')) {
        
        case 'info_page':
        
            // --- ESTADO de FIRtro ---
            //     -----------------------------------------
            //  1  Vol: -32.0   Hr: 34.0     Bal: -2  Stereo
            //  2  Bass: -2     Treb: -3     SysEQ  DRC  PEQ
            //  3  P: preset_name            LOUD   xover:mp
            //     -----------------------------------------
            //  4  I: input_name       ::plause::     44100
            //     -----------------------------------------

            // LINEA 1:
            if ($php_data['muted'] == false)    $("#info_vol").text("Vol: " + $php_data["level"]);
            else                                $("#info_vol").text("Vol: MUTE");

            $("#info_hro").text("Hr: " + $php_data["headroom"]);

            $("#info_bal").text("Bal: " + $php_data["balance"]);
                        
            // LINEA 2:
            $("#info_bas").text("Bass: " + $php_data["bass"])
            $("#info_tre").text("Treb: " + $php_data["treble"])

            if ($php_data["system_eq"] == true)     $("#info_seq").text("SysEQ");
            else                                    $("#info_seq").text(" --  ");

            if ($php_data["drc_eq"] != "0")         $("#info_drc").text("DRC");
            else                                    $("#info_drc").text(" - ");

            if ( ($php_data['peq'] != "") && ($php_data['peqdefeat'] != true) ) $("#info_peq").text("PEQ");
            else                                                                $("#info_peq").text(" - ");
            
            // LINEA 3:
            $("#info_pre").text("Preset: " + $php_data["preset"])
            if ($php_data['loudness_track']==true)  $("#info_lou").text("LOUD");
            else                                    $("#info_lou").text("    ");
            if ($php_data['mono'] == "on")          $("#info_ste").text("  MONO");
            else                                    $("#info_ste").text("Stereo");

            // LINEA 4:
            $("#info_inp").text($php_data["input_name"].toUpperCase())
            $("#info_fs").text($php_data["fs"])
            $("#info_xov").text("xo: " + $php_data["filter_type"])
            
            // --- INFO_PLAYER (metadatos) ---
            $player = $php_data['input_name'];
            if ($player.indexOf("tdt") !== -1)    $player = "mplayer"; 
            $artist = $php_data[$player].artist;
            $album = $php_data[$player].album;
            $title = $php_data[$player].title;
            $state = $php_data[$player].state;
            if ($artist == "")  $artist = "--";
            if ($album == "")   $album = "--";
            if ($title == "")   $title = "--";
            $("#info_artist").text($artist)
            $("#info_album").text($album)
            $("#info_title").text($title)
            $("#info_sta").text("::" + $state + "::");
            
            break;
        
        case 'level_page':
        
            if ($("#vol_slider").attr("value") != $php_data['level']) {
                $("#vol_slider").attr("value", $php_data['level']).slider("refresh");
            }
            // se redondea el alcance del slider para que no envíe valores con decimales ligados a
            // los decimales de maxlevel_i (el tope de volumen proporcionado por el server)
            if ($("#vol_slider").attr("max") != Math.round($php_data['maxlevel_i'])) {
                $("#vol_slider").attr("max", Math.round($php_data['maxlevel_i']));
                $("#vol_slider").attr("min", Math.round($php_data['maxlevel_i']) - $config['vol_slider_hr']);
                $("#vol_slider").slider("refresh");
            }

            if ($php_data['muted'] == true) {
                $("#level_display1").text("Volume: " + $php_data["level"] + " dB (MUTED)");
            }
            else {
                //$("#level_display1").text("Volume: " + $php_data["level"] + " dB (HR: " + $php_data["headroom"] + " dB)"); 
                $("#level_display1").text("VOL " + $php_data["level"] + " dB"
                                          + " / Hr " + $php_data["headroom"] + " dB"
                                          + " / Bal " + $php_data["balance"]
                                          ); 
            }
            
            $("#level_display21").text("FS: " + $php_data["fs"] + " Hz");
            
            if ($php_data['loudness_track']==true)  $("#level_display22").text("Loudness: ON");
            else                                    $("#level_display22").text("Loudness: OFF");
            
            $("#level_display31").text("DRC: " + $php_data["drc_eq"]);
            
            if ($php_data["system_eq"] == false)    $system_eq = "OFF";
            else                                    $system_eq = "ON";
            
            $("#level_display32").text("SysEQ: " +          $system_eq);
            $("#level_display41").text("Bass: " +           $php_data["bass"]);
            $("#level_display42").text("Treble: " +         $php_data["treble"]);
            $("#level_display51").text("Input: " +          $php_data["input_name"]);
            $("#level_display52").text("Filter type: " +    $php_data["filter_type"]);
            
            // MONO
            if ($php_data['mono'] == "on")      $("#level_display53").text("- MONO -");
            else                                $("#level_display53").text("- stereo -");
            
            // PRESETS
            $("#level_display54").text("Preset: " + $php_data["preset"]);            
            
            // PEQ
            if ($php_data['peq'] != "off") {
                $("#level_display55").text("PEQ: ON");
                if ($php_data['peqdefeat']) {
                    $("#level_display55").text("PEQ: DEFEAT");
                }
            }
            else {
                $("#level_display55").text("(no peq)");
            }
            
            // Array de warnings
            if ($php_data['warnings'] != "") {
                $php_data['warnings'].forEach(function(item) {
                if ($first_item) {
                    $("#level_display6").text("Warning: "+item);
                    $first_item=false;
                }
                else $("#level_display6").append("<br/>"+item);
                });    
            }
            else $("#level_display6").text("");

            break;

        case 'drc_page':
            
            $("#drc_display").empty();
            if ($php_data['muted'] == true) $("#drc_display").text("Volume: " + $php_data["level"] + " dB (MUTED)");
            else $("#drc_display").text("Volume: " + $php_data["level"] + " dB (HR: " + $php_data["headroom"] + " dB)");

            // Switch de control de SystemEQ
            if ($php_data['system_eq'] == true) {
                $("#drc_display").append("<br/>SysEQ: ON");
                $("#syseq_switch").attr("value", "on").slider("refresh");
            }
            else {
                $("#drc_display").append("<br/>SysEQ: OFF");
                $("#syseq_switch").attr("value", "off").slider("refresh");
            }
            
            // Incluimos informacion del PEQ en el display de la seccion DRC:
            // y un switch de control de PEQ.
            // $("#drc_display").append(" --- DRC: " + $php_data["drc_eq"] + "/" + ($php_data["drc_index"]).toString());
            drcinfo = ""
            if ($php_data['peq'] != "off") {
                drcinfo = " - PEQ: ON";
                $("#peq_switch").attr("value", "on").slider("refresh");
                if ($php_data['peqdefeat']) {
                    drcinfo = " - PEQ: DEFEAT";
                    $("#peq_switch").attr("value", "off").slider("refresh");
                }
            }
            else {
                drcinfo = " - (no peq)";
                $("#peq_switch").attr("value", "off").slider("refresh");
            }
            $("#drc_display").append(" - DRC: " + $php_data["drc_eq"] + "/" 
                                     + ($php_data["drc_index"]).toString() + drcinfo);
            
            // Array de warnings
            //if ($php_data['warnings'] != "") $("#drc_display").append("<br/>Warning: "+$php_data['warnings']);
            if ($php_data['warnings'] != "") {
                $php_data['warnings'].forEach(function(item) {
                if ($first_item) {
                    $("#drc_display").append("<br/>Warning: "+item);
                    $first_item=false;
                }
                else $("#drc_display").append("<br/>"+item);
                });    
            }
            // Actualizacion del grafico de tonos
            // Ojo con una cosa. La unica forma que he encontrado de cambiar la serie de datos y actualizar el grafico es haciendo esto:
            // $tone_plot.data=[$plot_data]
            // $tone_plot.replot([$plot_data]);
            // Otras formas como pasar la variable al crear el objeto, no funcionan.
            // La primera linea realmente solo hace falta una vez, ya que al igualar las propiedades se crea un enlace con la variable, no se copia
            // Si la variable cambia, basta hacer un replot y ya se actualiza. Esta linea se podria poner en el codigo de inicializacion de la pagina.
            // Precisamente por esto, si queremos actualizar solo si es necesario, debemos crear una variable temporal ($plot_data_new) paa ver si los datos han cambiado, ya que si se hace
            // JSON.stringify($tone_plot.data) !== JSON.stringify([$plot_data_new])
            // Da siempre False, aunque los datos no se visualicen actualizados
            
            // Datos para el grafico.
            $.each($php_data['freq_i'], function(index, value) {
                $plot_data_new[index]=[value, $php_data['drc2_r_mag_i'][index]];
                //console.log (tone_data[index]);
            });
            
            // Vemos si han cambiado
            if (JSON.stringify($plot_data_new) !== JSON.stringify($syseq_r_plot_data)) {
                $syseq_r_plot_data=$plot_data_new.slice();
                $syseq_r_plot.data=[$syseq_r_plot_data]; // Esta es la linea que slo hace falta asignar una vez al grafico
                $syseq_r_plot.replot([$syseq_r_plot_data]); // En el replot hay que pasarle la variable tamben, sino no funciona
                //console.log ("Grafico de EQ sistema actualizado");
            }
            
            // Datos para el grafico. Los guardamos en una variable nueva
            $.each($php_data['freq_i'], function(index, value) {
                $plot_data_new[index]=[value, $php_data['drc2_l_mag_i'][index]];
                //console.log (tone_data[index]);
            });
            
            // Vemos si han cambiado
            if (JSON.stringify($plot_data_new) !== JSON.stringify($syseq_l_plot_data)) {
                $syseq_l_plot_data=$plot_data_new.slice();
                $syseq_l_plot.data=[$syseq_l_plot_data]; // Esta es la linea que slo hace falta asignar una vez al grafico
                $syseq_l_plot.replot([$syseq_l_plot_data]); // En el replot hay que pasarle la variable tamben, sino no funciona
                //console.log ("Grafico de EQ sistema actualizado");
            }
            
            break;
            
        case 'tone_page':
        
            $("#tone_display").empty();
            if ($php_data['muted'] == true) 
                $("#tone_display").text("Volume: " + $php_data["level"] + " dB (MUTED)");
            else
                $("#tone_display").text("Volume: " + $php_data["level"] + " dB (HR: " + $php_data["headroom"] + " dB)");
            
            $("#tone_display").append("<br/>Bass: " + $php_data["bass"] + " --- Treble: " + $php_data["treble"]);
            
            // traslado del balance aqui:
            $("#tone_display").append("<br/>Balance: " + $php_data["balance"]);
            
            //if ($php_data['warnings'] != "") $("#tone_display").append("<br/>Warning: "+$php_data['warnings']);
            // Array de warnings
            if ($php_data['warnings'] != "") {
                $php_data['warnings'].forEach(function(item) {
                if ($first_item) {
                    $("#tone_display").append("<br/>Warning: "+item);
                    $first_item=false;
                }
                else $("#tone_display").append("<br/>"+item);
                });    
            }
            
            // Datos para el grafico. Los guardamos en una variable nueva
            $.each($php_data['freq_i'], function(index, value) {
                $plot_data_new[index]=[value, $php_data['tone_mag_i'][index]];
                //console.log (tone_data[index]);
            });
            
            // Vemos si han cambiado
            if (JSON.stringify($plot_data_new) !== JSON.stringify($tone_plot_data)) {
                $tone_plot_data=$plot_data_new.slice();
                $tone_plot.data=[$tone_plot_data]; // Esta es la linea que slo hace falta asignar una vez al grafico
                $tone_plot.replot([$tone_plot_data]); // En el replot hay que pasarle la variable tamben, sino no funciona
                //console.log ("Grafico de tonos actualizado");
            }

            // Slider de balance (antes en level_page)
            if ($("#bal_slider").attr("max") != $php_data['balance_variation']) {
                $("#bal_slider").attr("max", $php_data['balance_variation']).slider("refresh");
            }
            if ($("#bal_slider").attr("min") != -$php_data['balance_variation']) {
                $("#bal_slider").attr("min", -$php_data['balance_variation']).slider("refresh");
            }
            if ($("#bal_slider").attr("value") != $php_data['balance']) {
                $("#bal_slider").attr("value", $php_data['balance']).slider("refresh");
            }
            
                       
            break;

        case 'loudness_page':
        
            if ($("#loudness_slider").attr("value") != $php_data['loudness_ref']) $("#loudness_slider").attr("value",$php_data['loudness_ref']).slider("refresh");
            $("#loudness_display").empty();
            if ($php_data['muted'] == true) $("#loudness_display").text("Volume: " + $php_data["level"] + " dB (MUTED)");
            else $("#loudness_display").text("Volume: " + $php_data["level"] + " dB (HR: " + $php_data["headroom"] + " dB)");
            
            if ($php_data['loudness_track']==true) {            
                $("#loudness_display").append("<br/>Loudness " + $php_data["loudness_level_info"]);
                $("#loudness_switch").attr("value", "on").slider("refresh");                
            }
            else  {
                $("#loudness_display").append("<br/>Loudness OFF");
                $("#loudness_switch").attr("value", "off").slider("refresh");
            }
            //if ($php_data['warnings'] != "") $("#loudness_display").append("<br/>Warning: "+$php_data['warnings']);
            // Array de warnings
            if ($php_data['warnings'] != "") {
                $php_data['warnings'].forEach(function(item) {
                if ($first_item) {
                    $("#loudness_display").append("<br/>Warning: "+item);
                    $first_item=false;
                }
                else $("#loudness_display").append("<br/>"+item);
                });    
            }
            // Datos para el grafico. Los guardamos en una variable nueva
            $.each($php_data['freq_i'], function(index, value) {
                $plot_data_new[index]=[value, $php_data['loudeq_mag_i'][index]];
                //console.log (tone_data[index]);
            });
            
            // Vemos si han cambiado
            if (JSON.stringify($plot_data_new) !== JSON.stringify($loudeq_plot_data)) {
                $loudeq_plot_data=$plot_data_new.slice();
                $loudeq_plot.data=[$loudeq_plot_data]; // Esta es la linea que slo hace falta asignar una vez al grafico
                $loudeq_plot.replot([$loudeq_plot_data]); // En el replot hay que pasarle la variable tamben, sino no funciona
                //console.log ("Grafico de loudness actualizado");
            }
            break;

        case 'inputs_page':
        
            $("#input_display").empty();
            if ($php_data['muted'] == true) $("#input_display").text("Volume: " + $php_data["level"] + " dB (MUTED)");
            else $("#input_display").text("Volume: " + $php_data["level"] + " dB (HR: " + $php_data["headroom"] + " dB)");
            $("#input_display").append("<br/>Input: " + $php_data["input_name"] + " (" + $php_data["input_gain"] + " dB)" );
            // Array de warnings
            if ($php_data['warnings'] != "") {
                $php_data['warnings'].forEach(function(item) {
                if ($first_item) {
                    $("#input_display").append("<br/>Warning: "+item);
                    $first_item=false;
                }
                else $("#input_display").append("<br/>"+item);
                });    
            }
            break;


        // Seccion fusilada de inputs_page
        case 'presets_page':

            $("#preset_display").empty();
            if ($php_data['muted'] == true) $("#preset_display").text("Volume: " + $php_data["level"] + " dB (MUTED)");
            else $("#preset_display").text("Volume: " + $php_data["level"] + " dB (HR: " + $php_data["headroom"] + " dB)");
            $("#preset_display").append("<br/>Preset: " + $php_data["preset"] );
            // Array de warnings
            if ($php_data['warnings'] != "") {
                $php_data['warnings'].forEach(function(item) {
                if ($first_item) {
                    $("#preset_display").append("<br/>Warning: "+item);
                    $first_item=false;
                }
                else $("#preset_display").append("<br/>"+item);
                });    
            }
            break;

        case 'media_page':
        
            $("#media_display").empty();
            if ($php_data['muted'] == true) $("#media_display").text("Volume: " + $php_data["level"] + " dB (MUTED)");
            else $("#media_display").text("Volume: " + $php_data["level"] + " dB (HR: " + $php_data["headroom"] + " dB)");
            $("#media_display").append("<br/>Input: " + $php_data["input_name"] + " (" + $php_data["input_gain"] + " dB)" );
            // Array de warnings
            if ($php_data['warnings'] != "") {
                $php_data['warnings'].forEach(function(item) {
                if ($first_item) {
                    $("#media_display").append("<br/>Warning: "+item);
                    $first_item=false;
                }
                else $("#media_display").append("<br/>"+item);
                });    
            }
            break;

    default: break;
    }
}

// Actualizacion de los datos que contienen los gráficos
function update_plot(){
    switch ($.mobile.activePage.attr('id')) { // Página activa del documento
        case 'drc_page':
            $syseq_r_plot.replot();
            $syseq_l_plot.replot();
            break;
        case 'tone_page':
            $tone_plot.replot();
            break;
        case 'loudness_page':
            $loudeq_plot.replot();
            break;
    }
}

/////////////////////////////////////////
////////*** MANEJO DE EVENTOS ***////////
/////////////////////////////////////////

// Según la doc de JQuery se debe usar el método "$(document).on('pageinit', function(){" 
// en vez de "$(document).on('ready', function(event){"
// para asegurarse de que la página esta siempre lista
// http://jquerymobile.com/test/docs/api/events.html
// Pero OjO, porque este evento se produce por cada inicialización de la página, 
// cuando pinchamos por primera vez, así que hay que filtrar por página
// para evitar asignar la misma función mas de una vez al mismo control.

// "$(document).on('ready', function(event){" se ejecuta SOLO la primera vez que se carga el documento, 
// con la página de inicio. Aqui se define la función por defecto para todos los botones, 
// y como no se usa ningún ID ni nombre, funciona para todas las páginas y simplificamos código.

// Atención, como usamos posteriormete el evento 'pageinit' para código especifíco de cada página, 
// debe tenerse en cuenta que primero se produce el envento 'pageinit' (una vez por página)
// y luego 'ready' (solo la primera vez que se abre el documento, sea la página que sea). 
// Esto puede influir en donde se deben declarar ciertas variables

$(document).on('ready', function(event){
    // Oculta el textbox del slider
    //$("input.ui-slider-input").hide()

    // Deshabilitamos el zoom en los botones
    $('input[type="submit"]').nodoubletapzoom();
    
    // http://zsprawl.com/iOS/2012/05/completely-disabling-zoom-in-jquery-mobile-1-1-0/
    //$.extend($.mobile.zoom, {locked:true, enabled:false});
    
    // Capturamos todos los botones del formulario tipo submit.
    // Se envía su nombre al código PHP, donde se interpretará la acción correspondiente.
    $('input[type="submit"]').click(function(event) {
        //var theName = $.trim($("#theName").val());
        //var $button_name=event.currentTarget.name;
        var $button_name = event.currentTarget.name;
        var $button_value = event.currentTarget.value; //Es lo mismo que: var button= $(this).attr('name');
        // Excepciones:
        // 1- Si la página es la del navegador:
        if ($.mobile.activePage.attr('id')=="media_page") {
            // Navegador: Enviamos como valor el tipo de control (auto, mpd, cd, etc..)
            $button_value = $("#media_page input[name=media_select]:checked").attr("value");
            // Excepto si es auto, que enviamos la entrada activa
            // Mejor no coger el valor del selector de entradas, porque si no se ha entrado previamente en la página, no está inicializado
            //if ($button_value == "auto") $button_value=$("#inputs_page input[name='input_select']:checked").attr("value");
            // Asi que lo cogemos del array recibido del servidor
            if ($button_value == "auto") $button_value=$php_data['input_name'];
        }        
        // 2- Si el boton es el de salvar configuracion
        if ($button_name == "save_config") {
            $button_value=$config_changes;
            $('#save_config').dialog('close');
            console.log ("New config saved!");
        }
        // 3- Si el boton es el de cancelar la configuracion
        if ($button_name == "cancel_config") {
            restore_settings(); // Restauramos los valores
            $('#scancel_config').dialog('close'); // Cerramos el cuadro de dialogo
            $.mobile.navigate( "#level_page" ); // Volvemos a la pagina de inicio
            return; // No solicitamos nada al server
        }
        
        send_command (event.currentTarget.name, $button_value);
        event.preventDefault();
    });
            
    // Esto se usa para hacer el resize de los gráficos. Algunos exploradores generan eventos continuos mientras se estan redimensionando
    // creando una carga de de trabajo innecesaria. Otros sin embargo solo generan un evento cuando acaban de redimensionarse.
    // Para solucionar todos los casos, pongo un timer de espera ($resize_timeout) antes de hacer el resize del gráfico
    var $resize_timer;
    $(window).resize(function() {
        clearTimeout($resize_timer);
        $resize_timer = setTimeout(function() {
            update_plot();
        }, $resize_timeout);
    });
    
    // Establecemos el tema especificado en el config
    if ($config['global_theme'] != "" && $config['global_theme'] != "default") changeGlobalTheme($config['global_theme']);
    
    // Arrancamos el auto update
    if ($config['auto_update'] == true) auto_update();
});

// Función genérica de inicialización de página. Poner aqui las funciones comunes para todas.
// Se ejecuta la primera vez que se carga cada página.
// OjO con el orden de los eventos, ver notas en función anterior.
$(document).on('pageinit', function(){
    //changeGlobalTheme($config['global_theme']);    
});

// Inicializaciones por página. Se ejecutan la primera vez que se carga la página.
$(document).on('pageinit', '#level_page', function(){

    // También podemos hacer una única funcion generica pageinit:
    // $(document).on('pageinit', function(){
    // y filtrar dentro por el id de la página, usando la variable "this"
    // var $page = this;
    // alert ($page.id);

    // También existe $(this)
    // $() is the jQuery constructor function.
    // this is a reference to the DOM element of invocation.
    // so basically, in $(this), you are just passing the this in $() as a parameter so that you could call jQuery methods and functions.
    
    // Slider de volumen. Se envía el nombre y el valor al código PHP cada vez que cambie
    $('#vol_slider').on('slidestop', function(event) {
        //var $slider_name=event.currentTarget.name;
        //var $value=event.currentTarget.value;
        send_command (event.currentTarget.name, event.currentTarget.value);
        event.preventDefault();
    });
    
});

$(document).on('pageinit', '#drc_page', function(){

    // Switch de SysEQ. Se envía el nombre y el valor al código PHP
    $('#syseq_switch').on('slidestop', function(event) {
        send_command (event.currentTarget.name, event.currentTarget.value);
        event.preventDefault();
    });
    
    //Switch de PEQ. Se envía el nombre y el valor al código PHP            *** PEQ ***
    $('#peq_switch').on('slidestop', function(event) {
        send_command (event.currentTarget.name, event.currentTarget.value);
        event.preventDefault();
    });
    
    // Creamos el objeto, con datos vacios. Posteriormente en la funcion update_controls() nos ocuparemos de actualizarlos.
    $syseq_r_plot=$.jqplot('syseq_r_chartdiv', [['']], $plot_options_drc);
    $syseq_l_plot=$.jqplot('syseq_l_chartdiv', [['']], $plot_options_drc);
});

$(document).on('pageinit', '#tone_page', function(){
        
    // Creamos el objeto, con datos vacios. Posteriormente en la funcion update_controls() nos ocuparemos de actualizarlos.
    $tone_plot=$.jqplot('tone_chartdiv', [['']], $plot_options);

    // Slider de balance. Se envía el nombre y el valor al código PHP cada vez que cambie
    $('#bal_slider').on('slidestop', function(event) {
        //var $slider_name=event.currentTarget.name;
        //var $value=event.currentTarget.value;
        send_command (event.currentTarget.name, event.currentTarget.value);
        event.preventDefault();
    });
});

$(document).on('pageinit', '#loudness_page', function(){

    // Slider y switch de loudness. Se envía el nombre y el valor al código PHP
    $('#loudness_slider, #loudness_switch').on('slidestop', function(event) {
        send_command (event.currentTarget.name, event.currentTarget.value);
        event.preventDefault();
    });
    
    // Creamos el objeto, con datos vacios. Posteriormente en la funcion update_controls() nos ocuparemos de actualizarlos.
    $loudeq_plot=$.jqplot('loudeq_chartdiv', [['']], $plot_options);
});

$(document).on('pageinit', '#inputs_page', function(){
    if ($php_data) {
        
        // Recorremos el array de entradas para añadir el código correspondiente al selector
        // OjO se usa el nombre de la entrada como id del selector para que luego sea mas sencillo de seleccionar
        // Por tanto NO puede haber dos entradas con el mismo nombre, lo cual es de esperar.
        $php_data['inputs'].forEach(function(item) {
                $('#input_select_cg').append('<input type="radio" name="input_select" id="input_select_' + item + '" value="' + item + '" />'+
                                   '<label for="input_select_' + item + '">'+item+'</label>');
        });
        // Marcamos la entrada que hay actualmente activa como seleccionada. Se escapan los espacios
        // Tambien se podria buscar por su valor: $('input[value="xxxx"]')
        //$("input[id='input_select_" + $current_input + "'] ").attr('checked', true);
        $("#input_select_" + $php_data['input_name'].replace(/( )/g, "\\\ ")).attr('checked', true);
        // Tenemos que invocar la acción de crear al div que contiene todo el selector
        // Sino no se muestra con el estilo predefinido
        $("#input_radiodiv").trigger("create");
        
        // Capturamos los eventos de cambio para enviar las ordenes correspondientes
        $("#inputs_page input[name='input_select']").on('change', function(event, ui) {
                send_command (event.currentTarget.name, event.currentTarget.value);
                //event.preventDefault();
        });
    }

});

$(document).on('pageinit', '#presets_page', function(){
    if ($php_data) {
        
        $php_data['lista_de_presets'].forEach(function(item) {
                $('#preset_select_cg').append('<input type="radio" name="preset_select" id="preset_select_' + item + '" value="' + item + '" />'+
                                   '<label for="preset_select_' + item + '">'+item+'</label>');
        });
        
        // Marcamos el radio del preset activo como seleccionado. Se escapan los espacios
        
        $("#preset_select_" + $php_data['preset'].replace(/( )/g, "\\\ ")).attr('checked', true);

        // creación de un divisor de botones de entrada radio
        $("#preset_radiodiv").trigger("create");
        
        // Capturamos los eventos de cambio para enviar las ordenes correspondientes
        $("#presets_page input[name='preset_select']").on('change', function(event, ui) {
                send_command (event.currentTarget.name, event.currentTarget.value);
                //event.preventDefault();
        });
    }

});

$(document).on('pageinit', '#media_page', function(){

    //$("#media_select_auto").attr('checked', true);
    var $keypad_timer;

    $('[name="keypad"]').on("click", function(event) {
        clearTimeout($keypad_timer);
        $keypad_value = $keypad_value + event.currentTarget.value
        $keypad_timer = setTimeout(function() {
            var $button_name = "keypad_" + $keypad_value;
            var $button_value = $("#media_page input[name=media_select]:checked").attr("value");
            if ($button_value == "auto") $button_value=$php_data['input_name'];
            //alert ($button_name + " --- " + $button_value);
            send_command ($button_name, $button_value);
            $keypad_value = "";
        }, $config['keypad_timeout']);
    });
});

$(document).on('pageinit', '#custom_page', function(){

    $("#custom_1").attr('value', $config['btn_txt_1']).button('refresh');
    $("#custom_2").attr('value', $config['btn_txt_2']).button('refresh');
    $("#custom_3").attr('value', $config['btn_txt_3']).button('refresh');
    $("#custom_4").attr('value', $config['btn_txt_4']).button('refresh');
    $("#custom_5").attr('value', $config['btn_txt_5']).button('refresh');
    $("#custom_6").attr('value', $config['btn_txt_6']).button('refresh');
    $("#custom_7").attr('value', $config['btn_txt_7']).button('refresh');
    $("#custom_8").attr('value', $config['btn_txt_8']).button('refresh');
    $("#custom_9").attr('value', $config['btn_txt_9']).button('refresh');
    // Tambien se puede hacer asi:
    //$("#custom_1").val($config['btn_txt_1']).button('refresh')
});

$(document).on('pageinit', '#config_page', function(){

    // Creamos la seccion de opciones de forma dinamica
    // A los campos que almacenan los valores les llamamos "config_option" para poteriormente poder capturar los eventos de todos ellos en caso de que sus valores cambien
    console.log("Reading options...");
    $.each($config_ws, function(section) {
        console.log(section);
        $('#config_cs').append('<div data-role="collapsible" id="'+section+'"><h3>'+capitalize(section)+'</h3><div id="'+section+'_content" data-role="content"></div>').trigger("create")
        if (section == "themes") {
            $themes_array = $config_ws['themes']['themes'].split(" ");
            //El primer elemento debería ser una cadena vacia, pero si no lo es, añado al final la opcion "default"
            if ($themes_array[0] == "") $themes_array[0] = "default";
                else $themes_array.push("default");
            $("#"+section+"_content").append('<select name="config_option" id="global_theme" data-icon="grid" data-native-menu="false"></select>').trigger("create");
            $themes_array.forEach(function(value) {
                if (value != "") $('#global_theme').append('<option value="'+value+'">'+value+'</option>');
            });
            // Comprobamos el tema seleccionado en la configuracion
            if ($.inArray($config_ws['themes']['global_theme'], $themes_array) == -1) alert ("global theme is not in themes list!");
            // Y se selecciona
            $("#global_theme").val($config_ws['themes']['global_theme']).selectmenu('refresh', true);
        }
        else {      
            $.each ($config_ws[section], function(option) {
                option_value=$config_ws[section][option]
                console.log("\t"+option+": "+option_value)
                $("#"+section+"_content").append('<div data-role="fieldcontain">'+
                                                    '<label for="'+option+'">'+option+':</label>'+
                                                    //'<input type="text" name="'+option+'" id="'+option+'" value="'+option_value+'">'+
                                                    '<input type="text" name="config_option" id="'+option+'" value="'+option_value+'">'+
                                                 '</div>').trigger("create");
            });
        }
    });
    
    // Manejo de temas
    $('#global_theme').on("change", function(event){
        var theme=event.currentTarget.value;
        //console.log("Tema seleccionado:", theme)
        if (theme == "" || theme == "default") {
            $.mobile.changePage( "#theme_info", { role: "dialog" } );
        }
        else setTimeout(function() {changeGlobalTheme(event.currentTarget.value);}, 100);
    });
    
    // Control de cambios de opciones. Los almacenamos en un objeto temporal
    $('#config_page [name="config_option"]').on("change", function(event){
        $config_changes[event.currentTarget.id] = event.currentTarget.value
        console.log("New value => " + event.currentTarget.id+": "+event.currentTarget.value)
    });
    
    // Como esta seccion se crea dinamicamente, hay que forzar que se aplique el tema por defecto una vez creados los elementos.
    if ($config_ws['themes']['global_theme'] != "default") changeGlobalTheme($config_ws['themes']['global_theme']);

});

// Capturamos el cambio de página, para actualizar contenido si procede
/*
pageinit
pagebeforeload = triggered before the load request (inside changepage) is made
pageload = triggered after the page was loaded
pagebeforechange = triggered before a changepage is made
pagechange = triggered after changepage is done
pagebeforeshow = triggered before the page is shown
pageshow = triggered when the page is shown
*/

$(document).on('pagechange', function(event){
    // Primero inicializamos la página con los valores actuales si los hay, para que no se haga tan lenta la primera carga
    //if (typeof $php_data !== "undefined") update_controls();
    if ($php_data) update_controls();
    // Ahora solicitamos al server el estado. Si las variables han cambiado, la propia función se encargará de actualizar los datos, sino no hará nada
    send_command( "status", "0");
});
