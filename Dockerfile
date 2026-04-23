# Copyright (c) HETDEX Data Team

ARG BASE_CONTAINER=quay.io/jupyter/scipy-notebook
FROM $BASE_CONTAINER

LABEL maintainer="Erin Mentuch Cooper <erin.hetdex@gmail.com>"

USER root

# Install Node.js 20 (required for Claude ACP)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    curl \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y nodejs \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Install Claude ACP agent for Jupyter AI personas
RUN npm install -g @zed-industries/claude-agent-acp

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
RUN pip install grip
RUN grip /home/jovyan/dexcube/README.md --export /home/jovyan/dexcube/README.html

RUN cp /home/jovyan/dexcube/README.html /home/jovyan/README.html && \
    mkdir -p /home/jovyan/.jupyter && \
    printf "c.ServerApp.root_dir = '/home/jovyan'\n" \
           "c.ServerApp.default_url = '/lab/tree/README.html'\n" \
    > /home/jovyan/.jupyter/jupyter_server_config.py

RUN echo "export PATH=$HOME/.local/bin:${PATH}" >> ~/.bashrc

# Install Jupyter AI with Anthropic and OpenAI backends
RUN pip install jupyter-ai
 
# Copy HETDEX context files for LLM-assisted analysis
COPY HETDEX_CONTEXT.md /home/jovyan/HETDEX_CONTEXT.md
COPY CLAUDE.md /home/jovyan/CLAUDE.md

WORKDIR /home/jovyan

USER root

RUN chown -R jovyan /home/jovyan/ && \
    chmod 777 /home/jovyan && \
    chmod -R 777 /home/jovyan/dexcube && \ 
    chmod -R 777 /home/jovyan/.config/ && \
    chmod -R 777 /home/jovyan/.cache/ && \
    chmod -R 777 /home/jovyan/work/

USER jovyan


