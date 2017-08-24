#!/bin/bash

level=$1

echo 'cfoa "f_hi_L" "hi_L" '$level' ; cfoa "f_hi_R" "hi_R" '$level' ; quit'| nc localhost 3000
lf
