<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<!-- For iOS web apps -->
<!-- http://developer.apple.com/library/ios/#documentation/AppleApplications/Reference/SafariWebContent/UsingtheViewport/UsingtheViewport.html -->
<!-- <meta name="viewport" content="width=device-width, initial-scale=1">  -->
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scaleable=no">
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<meta name="apple-mobile-web-app-title" content="FIRtro Mobile">

<title>FIRtro Mobile</title>

<!-- Temas de la pagina. Usar solo un tipo, o oficiales o a medida -->
<!-- Temas a medida incluyen los standard a,b,c,d,e. -->
<!-- http://jquerymobile.com/themeroller/ -->
<link rel="stylesheet" href="css/themes/custom/myTheme.min.css" />
<link rel="stylesheet" href="css/themes/default/jquery.mobile.structure-1.3.2.min.css" />

<!-- Temas oficiales -->
<!--<link rel="stylesheet" href="css/themes/default/jquery.mobile-1.2.0.min.css" /> -->

<!-- Hojas de estilo principales -->
<link href="css/jqm-docs.css" rel="stylesheet" type="text/css">
<link href="css/main.css" rel="stylesheet" type="text/css">

<!-- JQuery -->
<script src="js/jquery-1.8.3.min.js"></script>
<script src="js/jquery.mobile-1.3.2.min.js"></script>

<!-- Jqplot -->
<!--[if lt IE 9]><script language="javascript" type="text/javascript" src="excanvas.js"></script><![endif]-->
<script language="javascript" type="text/javascript" src="jqplot/jquery.jqplot.min.js"></script>
<script type="text/javascript" src="jqplot/plugins/jqplot.logAxisRenderer.min.js"></script>
<script type="text/javascript" src="jqplot/plugins/jqplot.canvasOverlay.min.js"></script>
<link rel="stylesheet" type="text/css" href="jqplot/jquery.jqplot.min.css" />

<!-- Configuracion -->
<script language="javascript" type="text/javascript">
    var $config=<?php echo json_encode(parse_ini_file("config/config.ini"))?>;
    var $config_ws=<?php echo json_encode(parse_ini_file("config/config.ini",True))?>;
    if ($config == false) alert('Error: Can not read configuration file');
</script>

<!-- Funciones -->
<script src="js/functions.js"></script>
</head>

<body>

    <!-- ********************** -->
    <!-- ** Página principal ** -->
    <!-- ********************** -->

    <div data-role="page" class="type-interior" id="level_page"> <!--class="type-home"-->

        <div data-role="header" data-theme="d">
            <h1 name="tittle">FIRtro</h1>
            <a href="#" data-icon="home" data-iconpos="notext" data-direction="reverse">Home</a>
            <a href="#config_page" data-icon="gear" data-iconpos="notext" data-direction="reverse" name="config">Config</a>
        </div><!-- /header -->
                  
        <div data-role="content">

            <div class="content-primary">
                <div data-role="content" id="level_display" class="display display2 ui-corner-all">
                    <div class="ui-grid-solo" id="level_display1">Waiting...</div>
                    <div class="ui-grid-a">
                        <div class="ui-block-a" id="level_display53" style="max-width:160px; min-width:130px"></div><!--mono-->
                        <div class="ui-block-b" id="level_display51"></div><!--input-->
                        <div class="ui-block-a" id="level_display32" style="max-width:160px; min-width:130px"></div><!--syseq-->
                        <div class="ui-block-b" id="level_display22"></div><!--loudness-->
                        <div class="ui-block-a" id="level_display31" style="max-width:160px; min-width:130px"></div><!--drc-->
                        <div class="ui-block-b" id="level_display55"></div><!--peq-->
                        <div class="ui-block-a" id="level_display41" style="max-width:160px; min-width:130px"></div><!--bass-->
                        <div class="ui-block-b" id="level_display42"></div><!--treble-->
                        <div class="ui-block-a" id="level_display21" style="max-width:160px; min-width:130px"></div><!--fs-->
                        <div class="ui-block-b" id="level_display52" style="max-width:160px; min-width:130px"></div><!--ftype-->
                    </div>
                  <div class="ui-grid-solo" id="level_display54" style="max-width:6400px; min-width:320px"></div><!--preset-->
                  
                  <div class="ui-grid-solo" id="level_display6"></div><!--warnings-->
                  
                </div>
                
                <p></p>
                <div style="text-align:left;">Volume</div>
                <hr></hr>
                <p></p>
                <div id="vol_div">
                <input type="range" name="vol_slider" id="vol_slider" value="-10" min="-30" max="0" data-highlight="true" readonly />
                </div>
                <div class="ui-grid-a">
                <div class="ui-block-a">
                  <input name="level_down" type="submit" id="level_down" value="1dB" data-icon="minus" />
                  <input name="level_down_3" type="submit" id="level_down_3" value="3dB" data-icon="minus" />
                </div>
                <div class="ui-block-b">
                  <input name="level_up" type="submit" id="level_up" value="1dB" data-icon="plus" data-iconpos="right" />
                  <input name="level_up_3" type="submit" id="level_up_3" value="3dB" data-icon="plus" data-iconpos="right" />
                </div>
                </div>
                <div class="ui-grid-solo">
                    <input name="mute" type="submit" value="Mute" />
                </div>
                <p></p>
                <div style="text-align:left;">Balance</div>
                <hr></hr>
                <p></p>
                <div id="bal_div">
                <input type="range" name="bal_slider" id="bal_slider" value="0" min="-12" max="12" data-highlight="false" readonly />
                </div>
                
            </div> <!--/content-primary -->

            <div class="content-secondary">
                <div data-role="collapsible" data-collapsed="true" data-theme="b" data-content-theme="d">
                    <h3>More...</h3> <!--Subtitulo para cuando esta contraido-->
                    <ul data-role="listview" data-theme="c" data-dividertheme="d">
                        <li data-role="list-divider">Sections</li>
                        <li class="ui-btn-active"><a href="#">Volume</a></li>
                        <li><a href="#drc_page">DRC</a></li>
                        <li><a href="#tone_page">Tone</a></li>
                        <li><a href="#loudness_page">Loudness</a></li>
                        <li><a href="#inputs_page">Inputs</a></li>
                        <li><a href="#presets_page">Presets</a></li>
                        <li><a href="#media_page">Media</a></li>
                        <li><a href="#custom_page">Custom</a></li>
                    </ul>
                </div>
            </div> <!--/content-secondary -->

        </div><!-- /content -->

        <div data-role="footer" class="footer-docs" data-theme="d">
            <div class="ui-grid-a">
                <div class="ui-block-a" style="width:40%; padding-right:0px"><p>&copy; FIRtro mobile</p></div>
                <div class="ui-block-b" style="width:60%; padding-left:0px ; text-align:right">
                </div>
            </div>
        </div><!-- /footer -->
                  
    </div><!-- /Página principal -->

    <!-- **************** -->
    <!-- ** Página DRC ** -->
    <!-- **************** -->

    <div data-role="page" class="type-interior" id="drc_page">

        <div data-role="header" data-theme="d">
            <h1 name="tittle">FIRtro</h1>
            <a href="#level_page" data-icon="home" data-iconpos="notext" data-direction="reverse">Home</a>
            <a href="#config_page" data-icon="gear" data-iconpos="notext" data-direction="reverse" name="config">Config</a>
        </div><!-- /header -->
                  
        <div data-role="content">

            <div class="content-primary">
                <div data-role="content" id="drc_display" class="display ui-corner-all">
                Waiting...
                </div>
                <p></p>
                <div class="containing-element">
                  <select name="syseq_switch" id="syseq_switch" data-role="slider">
                    <option value="off">SysEQ OFF</option>
                    <option value="on">SysEQ ON</option>
                  </select>
                  <select name="peq_switch" id="peq_switch" data-role="slider">          <!-- *** PEQ *** -->
                    <option value="off">PEQ OFF</option>
                    <option value="on">PEQ ON</option>
                  </select>
                </div>
                <hr>
                  <div class="ui-grid-a">
                    <div class="ui-block-a">
                      <input name="drc0" type="submit" id="drc0" value="DRC 0" data-icon="grid" />
                    </div>
                    <div class="ui-block-b">
                      <input name="drc1" type="submit" id="drc1" value="DRC 1" data-icon="grid" data-iconpos="right" />
                    </div>
                    <div class="ui-block-a">
                      <input name="drc2" type="submit" id="drc2" value="DRC 2" data-icon="grid" />
                    </div>
                    <div class="ui-block-b">
                      <input name="drc3" type="submit" id="drc3" value="DRC 3" data-icon="grid" data-iconpos="right" />
                    </div>
                  </div>
                  <div style="text-align:center;">L Channel</div>
                  <div id="syseq_l_chartdiv" style="height:200px; width:100%; margin: 0 auto; text-align:center;"></div>
                  <div style="text-align:center;">R Channel</div>
                  <div id="syseq_r_chartdiv" style="height:200px; width:100%; margin: 0 auto; text-align:center;"></div>
            </div> <!--/content-primary -->

            <div class="content-secondary">
                <div data-role="collapsible" data-collapsed="true" data-theme="b" data-content-theme="d">
                    <h3>More...</h3> <!--Subtitulo para cuando esta contraido-->
                    <ul data-role="listview" data-theme="c" data-dividertheme="d">
                        <li data-role="list-divider">Sections</li>
                        <li><a href="#level_page">Volume</a></li>
                        <li class="ui-btn-active"><a href="#">DRC</a></li>
                        <li><a href="#tone_page">Tone</a></li>
                        <li><a href="#loudness_page">Loudness</a></li>
                        <li><a href="#inputs_page">Inputs</a></li>
                        <li><a href="#presets_page">Presets</a></li>
                        <li><a href="#media_page">Media</a></li>
                        <li><a href="#custom_page">Custom</a></li>
                    </ul>
                </div>
            </div><!--/content-secondary -->

        </div><!-- /content -->

        <div data-role="footer" class="footer-docs" data-theme="d">
            <div class="ui-grid-a">
                <div class="ui-block-a" style="width:40%; padding-right:0px"><p>&copy; FIRtro mobile</p></div>
                <div class="ui-block-b" style="width:60%">
                    <div data-role="controlgroup" data-type="horizontal" class="footer_level" style="padding-left:0px">
                        <input name="level_down" type="submit" value="Vol" data-icon="minus" />
                        <input name="mute" type="submit" value="Mute" />
                        <input name="level_up" type="submit" value="Vol" data-icon="plus" data-iconpos="right" />
                    </div>
                </div>
            </div>
        </div><!-- /footer -->

    </div><!-- /Página DRC -->

    <!-- ****************** -->
    <!-- ** Página Tonos ** -->
    <!-- ****************** -->

    <div data-role="page" class="type-interior" id="tone_page">

        <div data-role="header" data-theme="d">
            <h1 name="tittle">FIRtro</h1>
            <a href="#level_page" data-icon="home" data-iconpos="notext" data-direction="reverse">Home</a>
            <a href="#config_page" data-icon="gear" data-iconpos="notext" data-direction="reverse" name="config">Config</a>
        </div><!-- /header -->

        <div data-role="content">

            <div class="content-primary">
                <div data-role="content" id="tone_display" class="display ui-corner-all">
                Waiting...
                </div>
                <p></p>
                  <div class="ui-grid-a">
                    <div class="ui-block-a">
                      <input name="bass_up" type="submit" id="bass_up" value="Bass" data-icon="plus" />
                    </div>
                    <div class="ui-block-b">
                      <input name="treble_up" type="submit" id="treble_up" value="Treble" data-icon="plus" data-iconpos="right" />
                    </div>
                    <div class="ui-block-a">
                      <input name="bass_down" type="submit" id="bass_down" value="Bass" data-icon="minus" />
                    </div>
                    <div class="ui-block-b">
                      <input name="treble_down" type="submit" id="treble_down" value="Treble" data-icon="minus" data-iconpos="right" />
                    </div>
                  </div>
                  <div class="ui-grid-solo">
                      <input name="eq_flat" type="submit" id="eq_flat" value="Flat" data-icon="delete" />
                  </div> 
                  <div id="tone_chartdiv" style="height:200px; width:100%; margin: 0 auto; text-align:center;"></div>
                  
            </div> <!--/content-primary -->

            <div class="content-secondary">
                <div data-role="collapsible" data-collapsed="true" data-theme="b" data-content-theme="d">
                        <h3>More...</h3> <!--Subtitulo para cuando esta contraido-->
                        <ul data-role="listview" data-theme="c" data-dividertheme="d">
                            <li data-role="list-divider">Sections</li>
                            <li><a href="#level_page">Volume</a></li>
                            <li><a href="#drc_page">DRC</a></li>
                            <li class="ui-btn-active"><a href="#">Tone</a></li>
                            <li><a href="#loudness_page">Loudness</a></li>
                            <li><a href="#inputs_page">Inputs</a></li>
                            <li><a href="#presets_page">Presets</a></li>
                            <li><a href="#media_page">Media</a></li>
                            <li><a href="#custom_page">Custom</a></li>
                        </ul>
                </div>
            </div><!--/content-secondary -->

        </div><!-- /content -->

        <div data-role="footer" class="footer-docs" data-theme="d">
            <div class="ui-grid-a">
                <div class="ui-block-a" style="width:40%; padding-right:0px"><p>&copy; FIRtro mobile</p></div>
                <div class="ui-block-b" style="width:60%">
                    <div data-role="controlgroup" data-type="horizontal" class="footer_level" style="padding-left:0px">
                        <input name="level_down" type="submit" value="Vol" data-icon="minus" />
                        <input name="mute" type="submit" value="Mute" />
                        <input name="level_up" type="submit" value="Vol" data-icon="plus" data-iconpos="right" />
                    </div>
                </div>
            </div>
        </div><!-- /footer -->

    </div><!-- /Página Tonos -->

    <!-- ********************* -->
    <!-- ** Página Loudness ** -->
    <!-- ********************* -->
            
    <div data-role="page" class="type-interior" id="loudness_page">
        <div data-role="header" data-theme="d">
            <h1 name="tittle">FIRtro</h1>
            <a href="#level_page" data-icon="home" data-iconpos="notext" data-direction="reverse">Home</a>
            <a href="#config_page" data-icon="gear" data-iconpos="notext" data-direction="reverse" name="config">Config</a>
        </div><!-- /header -->

        <div data-role="content">

            <div class="content-primary">
                <div data-role="content" id="loudness_display" class="display ui-corner-all">
                Waiting...
                </div>
                  <p></p>
                  <div class="containing-element">
                      <select name="loudness_switch" id="loudness_switch" data-role="slider">
                        <option value="off">Loud OFF</option>
                        <option value="on">Loud ON</option>
                      </select>
                  </div>
                  <hr>
                    <input type="range" name="loudness_slider" id="loudness_slider" value="0" min="-10" max="10" data-highlight="true" readonly/>
                  <div class="ui-grid-a">
                    <div class="ui-block-a">
                      <input name="loud_ref_down" type="submit" id="loud_ref_down" value="Level Ref" data-icon="minus" />
                    </div>
                    <div class="ui-block-b">
                      <input name="loud_ref_up" type="submit" id="loud_ref_up" value="Level Ref" data-icon="plus" data-iconpos="right" />                  
                    </div>
                  </div>
                  <div class="ui-grid-solo">
                    <input name="loud_ref_reset" type="submit" id="loud_ref_reset" value="Reset" data-icon="refresh" />
                  </div>
                  <div id="loudeq_chartdiv" style="height:200px; width:100%; margin: 0 auto; text-align:center;"></div>
            </div> <!--/content-primary -->
                     
            <div class="content-secondary">
                <div data-role="collapsible" data-collapsed="true" data-theme="b" data-content-theme="d">
                        <h3>More...</h3> <!--Subtitulo para cuando esta contraido-->
                        <ul data-role="listview" data-theme="c" data-dividertheme="d">
                            <li data-role="list-divider">Sections</li>
                            <li><a href="#level_page">Volume</a></li>
                            <li><a href="#drc_page">DRC</a></li>
                            <li><a href="#tone_page">Tone</a></li>
                            <li class="ui-btn-active"><a href="#">Loudness</a></li>
                            <li><a href="#inputs_page">Inputs</a></li>
                            <li><a href="#presets_page">Presets</a></li>
                            <li><a href="#media_page">Media</a></li>
                            <li><a href="#custom_page">Custom</a></li>
                        </ul>
                </div>
            </div> <!--/content-secondary -->

        </div><!-- /content -->

        <div data-role="footer" class="footer-docs" data-theme="d">
            <div class="ui-grid-a">
                <div class="ui-block-a" style="width:40%; padding-right:0px"><p>&copy; FIRtro mobile</p></div>
                <div class="ui-block-b" style="width:60%">
                    <div data-role="controlgroup" data-type="horizontal" class="footer_level" style="padding-left:0px">
                        <input name="level_down" type="submit" value="Vol" data-icon="minus" />
                        <input name="mute" type="submit" value="Mute" />
                        <input name="level_up" type="submit" value="Vol" data-icon="plus" data-iconpos="right" />
                    </div>
                </div>
            </div>
        </div><!-- /footer -->

    </div><!-- /Página Loudness -->

    <!-- ******************* -->
    <!-- ** Página Inputs ** -->
    <!-- ******************* -->
        
    <div data-role="page" class="type-interior" id="inputs_page">
        
        <div data-role="header" data-theme="d">
            <h1 name="tittle">FIRtro</h1>
            <a href="#level_page" data-icon="home" data-iconpos="notext" data-direction="reverse">Home</a>
            <a href="#config_page" data-icon="gear" data-iconpos="notext" data-direction="reverse" name="config">Config</a>
        </div><!-- /header -->

        <div data-role="content">

            <div class="content-primary">
                <div data-role="content" id="input_display" class="display ui-corner-all">
                Waiting...
                </div>
              <p></p>
              <div id="input_radiodiv">
                <fieldset data-role="controlgroup" id="input_select_cg" class="center-controlgroup">
                </fieldset>
              </div>
            </div> <!--/content-primary -->
                     
            <div class="content-secondary">
                <div data-role="collapsible" data-collapsed="true" data-theme="b" data-content-theme="d">
                        <h3>More...</h3> <!--Subtitulo para cuando esta contraido-->
                        <ul data-role="listview" data-theme="c" data-dividertheme="d">
                            <li data-role="list-divider">Sections</li>
                            <li><a href="#level_page">Volume</a></li>
                            <li><a href="#drc_page">DRC</a></li>
                            <li><a href="#tone_page">Tone</a></li>
                            <li><a href="#loudness_page">Loudness</a></li>
                            <li class="ui-btn-active"><a href="#">Inputs</a></li>
                            <li><a href="#presets_page">Presets</a></li>
                            <li><a href="#media_page">Media</a></li>
                            <li><a href="#custom_page">Custom</a></li>
                        </ul>
                </div>
            </div> <!--/content-secondary -->

        </div><!-- /content -->

        <div data-role="footer" class="footer-docs" data-theme="d">
            <div class="ui-grid-a">
                <div class="ui-block-a" style="width:40%; padding-right:0px"><p>&copy; FIRtro mobile</p></div>
                <div class="ui-block-b" style="width:60%">
                    <div data-role="controlgroup" data-type="horizontal" class="footer_level" style="padding-left:0px">
                        <input name="level_down" type="submit" value="Vol" data-icon="minus" />
                        <input name="mute" type="submit" value="Mute" />
                        <input name="level_up" type="submit" value="Vol" data-icon="plus" data-iconpos="right" />
                    </div>
                </div>
            </div>
        </div><!-- /footer -->

    </div><!-- /Página Inputs -->
    
    
    <!-- ************************* -->
    <!-- ** Página PRESETS Beta ** -->
    <!-- ************************* -->
        
    <div data-role="page" class="type-interior" id="presets_page">
        
        <div data-role="header" data-theme="d">
            <h1 name="tittle">FIRtro</h1>
            <a href="#level_page" data-icon="home" data-iconpos="notext" data-direction="reverse">Home</a>
            <a href="#config_page" data-icon="gear" data-iconpos="notext" data-direction="reverse" name="config">Config</a>
        </div><!-- /header -->

        <div data-role="content">

            <div class="content-primary">
                <div data-role="content" id="preset_display" class="display ui-corner-all">
                Waiting...
                </div>
              <p></p>
              <div id="preset_radiodiv">
                <fieldset data-role="controlgroup" id="preset_select_cg" class="center-controlgroup">
                </fieldset>
              </div>

            </div> <!--/content-primary -->
                     
            <div class="content-secondary">
                <div data-role="collapsible" data-collapsed="true" data-theme="b" data-content-theme="d">
                        <h3>More...</h3> <!--Subtitulo para cuando esta contraido-->
                        <ul data-role="listview" data-theme="c" data-dividertheme="d">
                            <li data-role="list-divider">Sections</li>
                            <li><a href="#level_page">Volume</a></li>
                            <li><a href="#drc_page">DRC</a></li>
                            <li><a href="#tone_page">Tone</a></li>
                            <li><a href="#loudness_page">Loudness</a></li>
                            <li><a href="#inputs_page">Inputs</a></li>
                            <li class="ui-btn-active"><a href="#">Presets</a></li>
                            <li><a href="#media_page">Media</a></li>
                            <li><a href="#custom_page">Custom</a></li>
                        </ul>
                </div>
            </div> <!--/content-secondary -->

        </div><!-- /content -->

        <div data-role="footer" class="footer-docs" data-theme="d">
            <div class="ui-grid-a">
                <div class="ui-block-a" style="width:40%; padding-right:0px"><p>&copy; FIRtro mobile</p></div>
                <div class="ui-block-b" style="width:60%">
                    <div data-role="controlgroup" data-type="horizontal" class="footer_level" style="padding-left:0px">
                        <input name="level_down" type="submit" value="Vol" data-icon="minus" />
                        <input name="mute" type="submit" value="Mute" />
                        <input name="level_up" type="submit" value="Vol" data-icon="plus" data-iconpos="right" />
                    </div>
                </div>
            </div>
        </div><!-- /footer -->

    </div><!-- /Página Presets -->


    <!-- ****************** -->
    <!-- ** Página Media ** -->
    <!-- ****************** -->

    <div data-role="page" class="type-interior" id="media_page">
        
        <div data-role="header" data-theme="d">
            <h1 name="tittle">FIRtro</h1>
            <a href="#level_page" data-icon="home" data-iconpos="notext" data-direction="reverse">Home</a>
            <a href="#config_page" data-icon="gear" data-iconpos="notext" data-direction="reverse" name="config">Config</a>
        </div><!-- /header -->

        <div data-role="content">
        
            <div class="content-primary" >
                <div data-role="content" id="media_display" class="display ui-corner-all">
                Waiting...
                </div>
                  <p></p>
                <fieldset data-role="controlgroup" data-type="horizontal" class="center-controlgroup" data-mini="true">
                    <input type="radio" name="media_select" id="media_select_auto" value="auto" checked="checked"/>
                    <label for="media_select_auto">AUTO</label>
                    <input type="radio" name="media_select" id="media_select_mpd" value="mpd"/>
                    <label for="media_select_mpd">MPD</label>
                    <input type="radio" name="media_select" id="media_select_cdda" value="cdda"/>
                    <label for="media_select_cdda">CDDA</label>
                    <input type="radio" name="media_select" id="media_select_tdt" value="tdt"/>
                    <label for="media_select_tdt">TDT</label>
                </fieldset>
                <p></p>
                <!-- <div data-role="collapsible" data-theme="b" data-content-theme="d" data-collapsed="false"> -->
                <div data-role="collapsible" data-theme="b" data-collapsed="false">
                    <h3>Media</h3>
                    <div class="ui-grid-a">
                        <div class="ui-block-a"><input name="play" type="submit" value="Play"/></div>
                        <div class="ui-block-b"><input name="pause" type="submit" value="Pause" /></div>
                        <div class="ui-block-a"><input name="stop" type="submit" value="Stop" /></div>
                        <div class="ui-block-b"><input name="eject" type="submit" value="Eject" /></div>
                        <div class="ui-block-a"><input name="prev" type="submit" value="|<" /></div>
                        <div class="ui-block-b"><input name="next" type="submit" value=">|" /></div>
                        <div class="ui-block-a"><input name="rw" type="submit" value="<<" /></div>
                        <div class="ui-block-b"><input name="ff" type="submit" value=">>" /></div>
                    </div>
                </div>
                <!-- <div data-role="collapsible" data-theme="b" data-content-theme="d" data-collapsed="true"> -->
                <div data-role="collapsible" data-theme="b" data-collapsed="true">
                <h3>Keypad</h3>
                    <div class="ui-grid-b">
                        <div class="ui-block-a"><button name="keypad" value=1>1</button></div>
                        <div class="ui-block-b"><button name="keypad" value=2>2</button></div>
                        <div class="ui-block-c"><button name="keypad" value=3>3</button></div>
                        <div class="ui-block-a"><button name="keypad" value=4>4</button></div>
                        <div class="ui-block-b"><button name="keypad" value=5>5</button></div>
                        <div class="ui-block-c"><button name="keypad" value=6>6</button></div>
                        <div class="ui-block-a"><button name="keypad" value=7>7</button></div>
                        <div class="ui-block-b"><button name="keypad" value=8>8</button></div>
                        <div class="ui-block-c"><button name="keypad" value=9>9</button></div>
                        <div class="ui-block-a"></div>
                        <div class="ui-block-b"><button name="keypad" value=0>0</button></div>
                        <div class="ui-block-c"></div>
                    </div>
                </div>
                
                <!-- <div data-role="collapsible" data-theme="b" data-content-theme="d" data-collapsed="true"> -->
                <div data-role="collapsible" data-theme="b" data-collapsed="true">
                <h3>Various</h3>
                    <div class="ui-grid-a fitted">
                      <div class="ui-block-a"><input name="cd-mpd" type="submit" value="cd->mpd"/></div>
                      <div class="ui-block-b"><input name="media-mpd" type="submit" value="usb->mpd"/></div>
                      <div class="ui-block-a"><input name="eject-cd" type="submit" value="eject cd"/></div>
                      <div class="ui-block-b"><input name="eject-usb" type="submit" value="eject usb"/></div>
					  </div>

                </div>
            </div> <!--/content-primary -->

            <div class="content-secondary">
                <div data-role="collapsible" data-collapsed="true" data-theme="b" data-content-theme="d">
                        <h3>More...</h3> <!--Subtitulo para cuando esta contraido-->
                        <ul data-role="listview" data-theme="c" data-dividertheme="d">
                            <li data-role="list-divider">Sections</li>
                            <li><a href="#level_page">Volume</a></li>
                            <li><a href="#drc_page">DRC</a></li>
                            <li><a href="#tone_page">Tone</a></li>
                            <li><a href="#loudness_page">Loudness</a></li>
                            <li><a href="#inputs_page">Inputs</a></li>
                            <li><a href="#presets_page">Presets</a></li>
                            <li class="ui-btn-active"><a href="#">Media</a></li>
                            <li><a href="#custom_page">Custom</a></li>
                        </ul>
                </div>
            </div> <!--/content-secondary -->

        </div><!-- /content -->

        <div data-role="footer" class="footer-docs" data-theme="d">
            <div class="ui-grid-a">
                <div class="ui-block-a" style="width:40%; padding-right:0px"><p>&copy; FIRtro mobile</p></div>
                <div class="ui-block-b" style="width:60%">
                    <div data-role="controlgroup" data-type="horizontal" class="footer_level" style="padding-left:0px">
                        <input name="level_down" type="submit" value="Vol" data-icon="minus" />
                        <input name="mute" type="submit" value="Mute" />
                        <input name="level_up" type="submit" value="Vol" data-icon="plus" data-iconpos="right" />
                    </div>
                </div>
            </div>
        </div><!-- /footer -->

    </div><!-- /Página Media -->

    <!-- ******************* -->
    <!-- ** Página Custom ** -->
    <!-- ******************* -->

    <div data-role="page" class="type-interior" id="custom_page">

        <div data-role="header" data-theme="d">
            <h1 name="tittle">FIRtro</h1>
            <a href="#level_page" data-icon="home" data-iconpos="notext" data-direction="reverse">Home</a>
            <a href="#config_page" data-icon="gear" data-iconpos="notext" data-direction="reverse" name="config">Config</a>
        </div><!-- /header -->

        <div data-role="content">
            <div class="content-primary" >
                <!--
                <div data-role="content" id="custom_display" class="display ui-corner-all">
                
                </div>
                <p></p>
                -->
                <div class="ui-grid-b fitted">
                  <div class="ui-block-a"><input id="custom_1" name="custom_1" type="submit" value="1" /></div>
                  <div class="ui-block-b"><input id="custom_2" name="custom_2" type="submit" value="2" /></div>
                  <div class="ui-block-c"><input id="custom_3" name="custom_3" type="submit" value="3" /></div>
                  <div class="ui-block-a"><input id="custom_4" name="custom_4" type="submit" value="4" /></div>
                  <div class="ui-block-b"><input id="custom_5" name="custom_5" type="submit" value="5" /></div>
                  <div class="ui-block-c"><input id="custom_6" name="custom_6" type="submit" value="6" /></div>
                  <div class="ui-block-a"><input id="custom_7" name="custom_7" type="submit" value="7" /></div>
                  <div class="ui-block-b"><input id="custom_8" name="custom_8" type="submit" value="8" /></div>
                  <div class="ui-block-c"><input id="custom_9" name="custom_9" type="submit" value="9" /></div>
                </div>

                <!-- PRESETS -->
                <p></p>
                <b><div class="ui-grid-solo" id="level_display56"></div></b>

            </div> <!--/content-primary -->

            <div class="content-secondary">
                <div data-role="collapsible" data-collapsed="true" data-theme="b" data-content-theme="d">
                    <h3>More...</h3> <!--Subtitulo para cuando esta contraido-->

                        <ul data-role="listview" data-theme="c" data-dividertheme="d">
                            <li data-role="list-divider">Sections</li>
                            <li><a href="#level_page">Volume</a></li>
                            <li><a href="#drc_page">DRC</a></li>
                            <li><a href="#tone_page">Tone</a></li>
                            <li><a href="#loudness_page">Loudness</a></li>
                            <li><a href="#inputs_page">Inputs</a></li>
                            <li><a href="#presets_page">Presets</a></li>
                            <li><a href="#media_page">Media</a></li>
                            <li class="ui-btn-active"><a href="#">Custom</a></li>
                        </ul>
                </div>
            </div> <!--/content-secondary -->

        </div><!-- /content -->

        <div data-role="footer" class="footer-docs" data-theme="d">
            <div class="ui-grid-a">
                <div class="ui-block-a" style="width:40%; padding-right:0px"><p>&copy; FIRtro mobile</p></div>
                <div class="ui-block-b" style="width:60%">
                    <div data-role="controlgroup" data-type="horizontal" class="footer_level" style="padding-left:0px">
                        <input name="level_down" type="submit" value="Vol" data-icon="minus" />
                        <input name="mute" type="submit" value="Mute" />
                        <input name="level_up" type="submit" value="Vol" data-icon="plus" data-iconpos="right" />
                    </div>
                </div>
            </div>
        </div><!-- /footer -->

    </div><!-- /Página Custom -->
  
    <!-- ******************* -->
    <!-- ** Página Config ** -->
    <!-- ******************* -->

    <div data-role="page" class="type-interior" id="config_page">

        <div data-role="header" data-theme="d">
            <h1 name="tittle">FIRtro</h1>
            <a href="#level_page" data-icon="home" data-iconpos="notext" data-direction="reverse">Home</a>
            <a href="#config_page" data-icon="gear" data-iconpos="notext" data-direction="reverse" name="config">Config</a>
        </div><!-- /header -->

        <div data-role="content">
            <div data-role="collapsible-set" data-theme="c" data-content-theme="d" id="config_cs"></div><!-- El contenido se crea de forma dinamica -->
            <div class="ui-grid-a">
                <div class="ui-block-a" style="text-align:right"><a href="#cancel_config" data-rel="dialog" data-role="button" data-icon="delete" data-inline="true">Cancel</a></div>
                <div class="ui-block-b" style="text-align:left"><a href="#save_config" data-rel="dialog" data-role="button" data-icon="check" data-inline="true">Save</a></div>
            </div>
        </div><!-- /content -->

        <div data-role="footer" class="footer-docs" data-theme="d">
            <div class="ui-grid-a">
                <div class="ui-block-a" style="width:40%; padding-right:0px"><p>&copy; FIRtro mobile</p></div>
                <div class="ui-block-b" style="width:60%">
                    <div data-role="controlgroup" data-type="horizontal" class="footer_level" style="padding-left:0px">
                        <input name="level_down" type="submit" value="Vol" data-icon="minus" />
                        <input name="mute" type="submit" value="Mute" />
                        <input name="level_up" type="submit" value="Vol" data-icon="plus" data-iconpos="right" />
                    </div>
                </div>
            </div>
        </div><!-- /footer -->

    </div><!-- /Página Config --> 
    
    <!-- ************** -->
    <!-- ** Dialogos ** -->
    <!-- ************** -->

    <div data-role="page" id="cancel_config">
        <div data-role="header" data-theme="d">
            <h1 name="tittle">Config</h1>
        </div><!-- /header -->
        <div data-role="content" style="text-align:center">
            <p>Cancel changes?</p>
            <input name="cancel_config" type="submit" value="Yes" data-icon="check" data-inline="true"/>
            <a data-rel="back" data-role="button" data-icon="delete" data-inline="true">No</a>
        </div><!-- /content -->
        
    </div><!-- /Página cancel_config -->
    
    <div data-role="page" id="save_config">
        <div data-role="header" data-theme="d">
            <h1 name="tittle">Config</h1>
        </div><!-- /header -->
        <div data-role="content" style="text-align:center">
            <p>Save changes?</p>
            <input name="save_config" type="submit" value="Yes" data-icon="check" data-inline="true" />
            <a data-rel="back" data-role="button" data-icon="delete" data-inline="true">No</a>
        </div><!-- /content -->
        
    </div><!-- /Página save_config -->
    
    <div data-role="page" id="theme_info">
        <div data-role="header" data-theme="d">
            <h1 name="tittle">Config</h1>
        </div><!-- /header -->
        <div data-role="content" style="text-align:center">
            <p>To load the default theme you must save it, and then reload the page</p>
            <a data-rel="back" data-role="button" data-icon="check" data-inline="true">OK</a>
        </div><!-- /content -->
        
    </div><!-- /Página theme_info -->
</body>
</html>
