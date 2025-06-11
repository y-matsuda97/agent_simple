FROM nvidia/cuda:12.2.2-devel-ubuntu22.04
USER root

ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm

RUN apt-get update && apt-get install -y \
    locales \
    vim less \
    wget \
    gcc-11 \
    g++-11 \
    python3.11 \
    python3-pip \
    git \
    && localedef -f UTF-8 -i ja_JP ja_JP.UTF-8 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && update-alternatives --set python /usr/bin/python3.11

RUN python -m pip install --upgrade pip setuptools \
    && python -m pip install jupyterlab

COPY .devcontainer/base-requirements.txt /tmp/base-requirements.txt
RUN pip install -r /tmp/base-requirements.txt

COPY .devcontainer/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN mkdir -p /work
WORKDIR /work