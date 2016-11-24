#!/bin/bash

echo '(i) Valores cargados en el EQ del preamplificador FIRtro:'
echo ''
echo 'lmc eq "c_eq0" info; lmc eq "c_eq1" info; quit' | nc localhost 3000
echo ''

