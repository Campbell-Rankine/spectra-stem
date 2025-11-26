FROM python:3.11-slim-bookworm AS base
# set environment
ENV WD="/root/spectra"
ENV DEBIAN_FRONTEND=noninteractive
USER root
WORKDIR $WD

# install dependencies
FROM base AS dependencies_install
RUN apt-get update -y && apt-get install -y cmake git pkg-config libsdl-pango-dev libglew-dev libpango1.0-dev \
                    pkg-config nasm texlive-latex-base portaudio19-dev python3-pyaudio libasound2-plugins \
                    libgif-dev libcairo2-dev libpango1.0-dev


FROM dependencies_install AS python_dependencies
# install python dependencies
COPY ./requirements.txt $WD/requirements.txt
RUN pip3 install -r $WD/requirements.txt

FROM python_dependencies AS hot_reload
# Copy local files expose port and run
COPY ./ $WD/
EXPOSE 7860
CMD [ "python3", "/root/spectra/app.py" ]