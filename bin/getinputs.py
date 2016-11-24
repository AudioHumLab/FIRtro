#!/usr/bin/python
#coding=utf-8
# from __future__ import with_statement # This isn't required in Python 2.6

from ConfigParser import RawConfigParser
from basepaths import *

inputs_path = config_folder + inputs_filename
inputs = RawConfigParser()
inputsfile = open(inputs_path)
inputs.readfp(inputsfile)
inputsfile.close

