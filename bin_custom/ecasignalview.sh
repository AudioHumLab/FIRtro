#!/bin/bash

p=$1

ecasignalview -f:f32,2 jack,$1 null

