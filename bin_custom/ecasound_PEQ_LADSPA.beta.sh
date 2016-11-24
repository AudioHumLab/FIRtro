#!/bin/bash

# NOTA:
# Esta es una VERSION BETA PARA INCLUIR UN PEQ ANTES DE BRUTEFIR
# SEP-2016: dispobible un script ecasound_PEQ_net.py con más funciones
# (ver FIRtro_con_PRESETS.pdf)


# tabla de equivalencias  BW / Q
# 1/2   0.5000    1/3   0.3333    1/4   0.2500    1/5   0.2000
# 1/6   0.1667    1/7   0.1429    1/8   0.1250    1/9   0.1111
# 1/10  0.1000    1/11  0.0909    1/12  0.0833    1/13  0.0769
# 1/14  0.0714    1/15  0.0667    1/16  0.0625    1/17  0.0588
# 1/18  0.0556    1/19  0.0526    1/20  0.0500    1/21  0.0476
# 1/22  0.0455    1/23  0.0435    1/24  0.0417    1/27  0.0370
# 1/30  0.0333

# Tabla de parametros para el plugin "filters" (4-band parametric filter)
# de Fons Adriansen & Nedko Aranaudov
# ** OjO separada exclusivamente por espacios **

# GLOBAL active,   gain:    ! he comprobado que las ganancias actuan correctamente en cada canal !
globaL="  0,        0.0  "
globaR="  0,        0.0  "

# L    ACT,    freq,    bw,      gain
peqL11=" 0,    10.0     1.0      0.0"
peqL12=" 0,    10.0     1.0      0.0"
peqL13=" 0,    10.0     1.0      0.0"
peqL14=" 0,    10.0     1.0      0.0"
peqL21=" 0,    10.0     1.0      0.0"
peqL22=" 0,    10.0     1.0      0.0"
peqL23=" 0,    10.0     1.0      0.0"
peqL24=" 0,    10.0     1.0      0.0"
peqL31=" 0,    10.0     1.0      0.0"
peqL32=" 0,    10.0     1.0      0.0"
peqL33=" 0,    10.0     1.0      0.0"
peqL34=" 0,    10.0     1.0      0.0"

# R    ACT,    freq,    bw,      gain
peqR11=" 0,    10.0     1.0      0.0"
peqR12=" 0,    10.0     1.0      0.0"
peqR13=" 0,    10.0     1.0      0.0"
peqR14=" 0,    10.0     1.0      0.0"
peqR21=" 0,    10.0     1.0      0.0"
peqR22=" 0,    10.0     1.0      0.0"
peqR23=" 0,    10.0     1.0      0.0"
peqR24=" 0,    10.0     1.0      0.0"
peqR31=" 0,    10.0     1.0      0.0"
peqR32=" 0,    10.0     1.0      0.0"
peqR33=" 0,    10.0     1.0      0.0"
peqR34=" 0,    10.0     1.0      0.0"

parL1=$globaL,$peqL11,$peqL12,$peqL13,$peqL14
parL1=${parL1// }  # limpia todos los espacios
parL2=$globaL,$peqL21,$peqL22,$peqL23,$peqL24
parL2=${parL2// }
parL3=$globaL,$peqL31,$peqL32,$peqL33,$peqL34
parL3=${parL3// }

parR1=$globaR,$peqR11,$peqR12,$peqR13,$peqR14
parR1=${parR1// }  # limpia todos los espacios
parR2=$globaR,$peqR21,$peqR22,$peqR23,$peqR24
parR2=${parR2// }
parR2=$globaR,$peqR31,$peqR32,$peqR33,$peqR34
parR2=${parR3// }

killall ecasound
sleep 2
ecasound -q --server -r -b:2048 -f:f32_le,1,44100 -G:jack,ecasound,notransport \
    -n:2xFonsA_4band_dualMono \
    -a:left \
        -i jack                  \
           -eli:1970,$parL1 \
           -eli:1970,$parL2 \
           -eli:1970,$parL3 \
        -o jack,brutefir:input-0 \
    -a:right \
        -i jack                  \
           -eli:1970,$parR1 \
           -eli:1970,$parR2 \
           -eli:1970,$parR3 \
        -o jack,brutefir:input-1 &

#----------------------------------------------------------------------------
# Puertos de entrada para control del plugin LV2:
# http://nedko.aranaudov.org/soft/filter/2/mono
#
#    Presets:
#
#    Port 2:    Symbol: active    Name: Active
#        Minimum: 0.000000    Maximum: 1.000000        Default: 0.000000
#
#    Port 3:    Symbol: gain    Name: Gain
#        Minimum: -20.000000    Maximum: 20.000000        Default: 0.000000
#
#    Port 4:    Symbol: active1    Name: Active1
#        Minimum: 0.000000    Maximum: 1.000000        Default: 0.000000
#
#    Port 5:    Symbol: freq1    Name: Frequency 1
#        Minimum: 20.000000    Maximum: 2000.000000    Default: 200.000000
#
#    Port 6:    Symbol: bandwidth1    Name: Bandwidth 1
#        Minimum: 0.125000    Maximum: 8.000000        Default: 1.000000
#
#    Port 7:    Symbol: gain1    Name: Gain 1
#        Minimum: -20.000000    Maximum: 20.000000        Default: 0.000000
#
#    Port 8:    Symbol: active2    Name: Active 2
#        Minimum: 0.000000    Maximum: 1.000000        Default: 0.000000
#
#    Port 9:    Symbol: frequency2    Name: Frequency 2
#        Minimum: 40.000000    Maximum: 4000.000000    Default: 400.000000
#
#    Port 10:    Symbol: bandwidth2    Name: Bandwidth 2
#        Minimum: 0.125000    Maximum: 8.000000        Default: 1.000000
#
#    Port 11:    Symbol: gain2    Name: Gain 2
#        Minimum: -20.000000    Maximum: 20.000000        Default: 0.000000
#
#    Port 12:    Symbol: active3    Name: Active 3
#        Minimum: 0.000000    Maximum: 1.000000        Default: 0.000000
#
#    Port 13:    Symbol: frequency3    Name: Frequency 3
#        Minimum: 100.000000    Maximum: 10000.000000    Default: 1000.000000
#
#    Port 14:    Symbol: bandwidth3    Name: Bandwidth 3
#        Minimum: 0.125000    Maximum: 8.000000        Default: 1.000000
#
#    Port 15:    Symbol: gain3    Name: Gain 3
#        Minimum: -20.000000    Maximum: 20.000000        Default: 0.000000
#
#    Port 16:    Symbol: active4    Name: Active 4
#        Minimum: 0.000000    Maximum: 1.000000        Default: 0.000000
#
#    Port 17:    Symbol: frequency4    Name: Frequency 4
#        Minimum: 200.000000    Maximum: 20000.000000    Default: 2000.000000
#
#    Port 18:    Symbol: bandwidth4    Name: Bandwidth 4
#        Minimum: 0.125000    Maximum: 8.000000        Default: 1.000000
#
#    Port 19:    Symbol: gain4    Name: Gain 4
#        Minimum: -20.000000    Maximum: 20.000000        Default: 0.000000
#


#----------------------------------------------------------------------------
#Puertos de entrada para control del plugin LADSPA:
#
#    "Filter"         toggled         default 0
#    "Gain"          -20 to 20        default 0
#    "Section 1"     toggled         default 0
#    "Frequency 1"     20 to 2000        default 200        logarithmic
#    "Bandwidth 1"     0.125 to 8        default 1        logarithmic
#    "Gain 1"         -20 to 20        default 0
#    "Section 2"     toggled         default 0
#    "Frequency 2"     40 to 4000        default 400        logarithmic
#    "Bandwidth 2"     0.125 to 8        default 1        logarithmic
#    "Gain 2"         -20 to 20        default 0
#    "Section 3"     toggled         default 0
#    "Frequency 3"     100 to 10000    default 1000    logarithmic
#    "Bandwidth 3"     0.125 to 8        default 1        logarithmic
#    "Gain 3"         -20 to 20        default 0
#    "Section 4"     toggled         default 0
#    "Frequency 4"     200 to 20000    default 2000    logarithmic
#    "Bandwidth 4"     0.125 to 8        default 1        logarithmic
#    "Gain 4"         -20 to 20        default 0
#
#

