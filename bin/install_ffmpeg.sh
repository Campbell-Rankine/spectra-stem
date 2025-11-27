#!/bin/bash

git clone https://github.com/FFmpeg/FFmpeg.git
cd /FFmpeg/configure
make -j4 && make install
cd ..
cd ..
