#!/bin/bash

git clone https://github.com/FFmpeg/FFmpeg.git
cd /FFmpeg/configure
RUN make -j4
RUN make install
cd ..
cd ..