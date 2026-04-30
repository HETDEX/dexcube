#!/bin/bash
set -e
mkdir -p /home/jovyan/.jupyter
chmod 770 /home/jovyan/.jupyter
touch /home/jovyan/.jupyter/mcp_settings.json
chmod 660 /home/jovyan/.jupyter/mcp_settings.json
exec "$@"

