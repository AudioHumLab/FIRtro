#!/bin/bash

if [ -z $1 ] ; then
    echo uso indicando la branch:
    echo "    bajaFIRtro.sh master|testing|xxx"
    echo
    exit 0
fi

branch=$1

mkdir /home/firtro/tmp > /dev/null 2>&1
cd /home/firtro/tmp
rm $branch.zip
rm -r FIRtro-$branch
wget https://github.com/AudioHumLab/FIRtro/archive/$branch.zip
unzip $branch.zip
cp -f FIRtro-$branch/.install/* .
cd
