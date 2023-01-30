#!/bin/bash

# Logical conditions:
# 0. If not already in virtualenv:
# 0.1. If virtualenv already exists activate it,
# 0.2. If not create it with global packages, update pip then activate it
# 1. If already in virtualenv: just give info
#
# Usage:
# Without arguments it will create virtualenv named .venv_vscode_antimony_virtual_env with python3 version
# $ ve
# or for a specific python version
# $ ve python3.10
# or for a specific python version and environment name;
# $ ve python3.10 ./.venv-diff

echo "script runs"

ve() {
    local py=${1:-python3}
    local venv="venv_vscode_antimony_virtual_env"

    local bin="${venv}/bin/activate"

    echo "running install virtual env"
    # If not already in virtualenv
    # $VIRTUAL_ENV is being set from $venv/bin/activate script
    sudo apt install python3.9-venv
    echo "Creating and activating virtual environment ${venv}"
    python3 -m venv ${venv} --system-site-packages
    echo "export PYTHON=${py}" >> ${bin}    # overwrite ${python} on .zshenv
    echo "Upgrading pip"
    sudo apt-get install python3-pip
    pip install --upgrade pip
    python3 -m pip --disable-pip-version-check install -t ./pythonFiles/lib/python --no-cache-dir --upgrade -r ./all-requirements.txt && success=1
}

ve "$@"