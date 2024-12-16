FROM ubuntu:22.04
MAINTAINER Niema Moshiri <niemamoshiri@gmail.com>
RUN apt-get update && apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y g++ gcc git python3 python3-dev python3-pip texlive-fonts-extra texlive-latex-extra texlive-xetex latexmk && \
    python3 -m pip install --upgrade --no-cache-dir --ignore-installed pip && \
    pip3 install --no-cache-dir --ignore-installed wheel && \
    pip3 install --no-cache-dir --ignore-installed jupyter-book && \
    apt-get autoremove -y && apt-get clean && \
    rm -rf ~/.cache /tmp/*
