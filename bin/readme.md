# spectra-stem/bin

---

Cache git pulls etc.

Dockerfile

# install ffmpeg frpm source (lightweight)

COPY ./bin/ $WD/bin/
WORKDIR $WD/bin/
RUN git clone https://github.com/FFmpeg/FFmpeg.git
WORKDIR $WD/bin/FFmpeg
RUN $WD/bin/FFmpeg/configure
RUN make -j4
RUN make install
WORKDIR $WD
