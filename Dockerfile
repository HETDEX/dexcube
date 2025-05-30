# Copyright (c) HETDEX Data Team

ARG BASE_CONTAINER=quay.io/jupyter/scipy-notebook:2024-11-04
FROM $BASE_CONTAINER

LABEL maintainer="Erin Mentuch Cooper <erin@astro.as.utexas.edu>"

USER root

RUN apt-get update && apt-get install -y poppler-utils

USER jovyan

RUN echo 'PS1="\w $ "' >> ~/.bashrc

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt


# Set working directory
WORKDIR ${HOME}/dexcube

# Copy repository contents into the container
COPY . ${HOME}/dexcube

# Change ownership to the notebook user
USER root
RUN chown -R ${NB_UID}:${NB_UID} ${HOME}
USER ${NB_USER}

# Install Python dependencies

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install tapipy --ignore-installed certifi
RUN pip install --upgrade jupyterlab jupyterlab_server jupyter_server traitlets nbformat

# Set the default command to start JupyterLab
CMD ["start.sh", "jupyter", "lab", "--NotebookApp.default_url=/lab/tree/notebooks/README.md"]

RUN export HOME='/home/jovyan'

RUN echo "export PATH=$HOME/.local/bin:${PATH}" >> ~/.bashrc

WORKDIR /home/jovyan

RUN chown -R jovyan /home/jovyan/ && \
    chmod 777 /home/jovyan && \ 
    chmod -R 777 /home/jovyan/.config/ && \
    chmod -R 777 /home/jovyan/.cache/matplotlib/ && \
    chmod -R 777 /home/jovyan/.cache/

USER jovyan