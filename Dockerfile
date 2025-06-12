# Copyright (c) HETDEX Data Team

ARG BASE_CONTAINER=quay.io/jupyter/scipy-notebook
FROM $BASE_CONTAINER

LABEL maintainer="Erin Mentuch Cooper <erin@astro.as.utexas.edu>"

USER root

RUN apt-get update && apt-get install -y poppler-utils

USER jovyan

RUN echo 'PS1="\w $ "' >> ~/.bashrc

WORKDIR /home/jovyan/dexcube

# Copy requirements before installing
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Change ownership to the notebook user
USER root
RUN chown -R ${NB_UID}:${NB_UID} ${HOME}
USER ${NB_USER}

# Install Python dependencies

RUN pip install tapipy --ignore-installed certifi
RUN pip install --upgrade jupyterlab jupyterlab_server jupyter_server traitlets nbformat

RUN export HOME='/home/jovyan'

RUN echo "export PATH=$HOME/.local/bin:${PATH}" >> ~/.bashrc

WORKDIR /home/jovyan

USER root

RUN chown -R jovyan /home/jovyan/ && \
    chmod 777 /home/jovyan && \
    chmod -R 777 /home/jovyan/dexcube && \ 
    chmod -R 777 /home/jovyan/.config/ && \
    chmod -R 777 /home/jovyan/.cache/ && \
    chmod -R 777 /home/jovyan/work/

USER jovyan


