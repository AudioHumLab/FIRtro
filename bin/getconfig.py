#!/usr/bin/python
#coding=utf-8
# from __future__ import with_statement # This isn't required in Python 2.6

from ConfigParser import RawConfigParser
from basepaths import *
import os
HOME = os.path.expanduser("~")

config_path = config_folder + config_filename
config = RawConfigParser()
configfile = open(config_path)
config.readfp(configfile)
configfile.close

#[misc]
level_on_startup =          config.get('misc', 'level_on_startup')
max_level_on_startup =      config.get('misc', 'max_level_on_startup')
gmax =                      config.getfloat('misc', 'gmax')
tone_defeat_on_startup =    config.getboolean('misc', 'tone_defeat_on_startup')

command_delay =             config.getfloat('misc', 'command_delay')
beep_options =              config.get('misc', 'beep_options')

enable_lcd =                config.getboolean('misc', 'enable_lcd')
lcd_info_timeout =          config.getfloat('misc', 'lcd_info_timeout')
lcd_opc =                   config.getfloat('misc', 'lcd_opc')

dummy_ports =               config.get('misc', 'dummy_ports')
pause_players =             config.getboolean('misc', 'pause_players')
resume_players =            config.getboolean('misc', 'resume_players')
jack_internal_monitors =    config.get('misc', 'jack_internal_monitors')
jack_external_monitors =    config.get('misc', 'jack_external_monitors')

#[presets]
default_preset =            config.get('presets', 'default_preset')

#[cards]
system_card =               config.get('cards', 'system_card')
external_cards =            config.get('cards', 'external_cards')
resampler =                 config.get('cards', 'resampler')
resamplingQ =               config.get('cards', 'resamplingQ')

#[path]
jack_path =                 config.get('path', 'jack_path')
jack_options =              config.get('path', 'jack_options')

brutefir_path =             config.get('path', 'brutefir_path')
brutefir_options =          config.get('path', 'brutefir_options')
brutefir_ports =            config.get('path', 'brutefir_ports')

control_path =              config.get('path', 'control_path')
control_output =            config.getint('path', 'control_output')
control_clear =             config.getboolean('path', 'control_clear')

syseq_path =                config.get('path', 'syseq_path')

load_ecasound =             config.getboolean('path', 'load_ecasound')
ecasound_path  =            config.get('path', 'ecasound_path')
ecasound_filters =          config.get('path', 'ecasound_filters')
ecasound_ports   =          config.get('path', 'ecasound_ports')

load_mpd =                  config.getboolean('path', 'load_mpd')
mpd_path =                  config.get('path', 'mpd_path')
mpd_options =               config.get('path', 'mpd_options')
mpd_volume_linked2firtro =  config.getboolean('path', 'mpd_volume_linked2firtro')

load_mplayer_tdt  =         config.getboolean('path', 'load_mplayer_tdt')
load_mplayer_cdda =         config.getboolean('path', 'load_mplayer_cdda')
mplayer_path =              config.get('path', 'mplayer_path')
mplayer_options =           config.get('path', 'mplayer_options')
cdda_fifo =                 HOME + "/cdda_fifo"
tdt_fifo  =                 HOME + "/tdt_fifo"

load_mopidy =               config.getboolean('path', 'load_mopidy')
mopidy_path =               config.get('path', 'mopidy_path')
mopidy_options =            config.get('path', 'mopidy_options')

load_shairport =            config.getboolean('path', 'load_shairport')
shairport_path =            config.get('path', 'shairport_path')
shairport_options =         config.get('path', 'shairport_options')

load_squeezeslave =         config.getboolean('path', 'load_squeezeslave')
squeezeslave_path =         config.get('path', 'squeezeslave_path')
squeezeslave_options =      config.get('path', 'squeezeslave_options')

load_jacktrip =             config.getboolean('path', 'load_jacktrip')
jacktrip_path =             config.get('path', 'jacktrip_path')
jacktrip_options =          config.get('path', 'jacktrip_options')

load_netjack =              config.getboolean('path', 'load_netjack')
netjack_path =              config.get('path', 'netjack_path')
netjack_options =           config.get('path', 'netjack_options')

load_client175 =            config.getboolean('path', 'load_client175')
client175_path =            config.get('path', 'client175_path')
client175_options =         config.get('path', 'client175_options')

load_mpdlcd =               config.getboolean('path', 'load_mpdlcd')
mpdlcd_path =               config.get('path', 'mpdlcd_path')
mpdlcd_options =            config.get('path', 'mpdlcd_options')

load_irexec =               config.getboolean('path', 'load_irexec')
irexec_path =               config.get('path', 'irexec_path')
irexec_options =            config.get('path', 'irexec_options')

#[net]
ip_address =                config.get('net', 'ip_address')
bfcli_address =             config.get('net', 'bfcli_address')
#port =                     config.getint('net', 'bfcli_port')
bfcli_port =                config.getint('net', 'bfcli_port')
control_address =           config.get('net', 'control_address')
control_port =              config.getint('net', 'control_port')

#[speakers]
loudspeaker =               config.get('speakers', 'loudspeaker')

#[equalizer]
freq_filename =             config.get('equalizer', 'frequencies')
loudness_mag_filename =     config.get('equalizer', 'loudness_mag_curves')
loudness_pha_filename =     config.get('equalizer', 'loudness_pha_curves')
treble_mag_filename =       config.get('equalizer', 'treble_mag_curves')
treble_pha_filename =       config.get('equalizer', 'treble_pha_curves')
bass_mag_filename =         config.get('equalizer', 'bass_mag_curves')
bass_pha_filename =         config.get('equalizer', 'bass_pha_curves')
syseq_mag_filename =        config.get('equalizer', 'syseq_mag_curve')
syseq_pha_filename =        config.get('equalizer', 'syseq_pha_curve')

step =                      config.getfloat('equalizer', 'step')
loudness_SPLref =           config.getfloat('equalizer', 'loudness_SPLref')
loudness_SPLmax =           config.getfloat('equalizer', 'loudness_SPLmax')
loudness_SPLmin =           config.getfloat('equalizer', 'loudness_SPLmin')
tone_variation =            config.getfloat('equalizer', 'tone_variation')
balance_variation =         config.getfloat('equalizer', 'balance_variation')
loudness_variation =        config.getfloat('equalizer', 'loudness_variation')
no_phase_xo =               config.get('equalizer', 'no_phase_xo')

syseq_mag_path =            config_folder + syseq_mag_filename
syseq_pha_path =            config_folder + syseq_pha_filename
loudness_mag_path =         config_folder + loudness_mag_filename
loudness_pha_path =         config_folder + loudness_pha_filename
treble_mag_path =           config_folder + treble_mag_filename
treble_pha_path =           config_folder + treble_pha_filename
bass_mag_path =             config_folder + bass_mag_filename
bass_pha_path =             config_folder + bass_pha_filename
freq_path =                 config_folder + freq_filename
