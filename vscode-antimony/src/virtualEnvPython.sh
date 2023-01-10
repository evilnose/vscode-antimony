#!/usr/bin/env bash

chmod a+x virtualEnvPython.sh

# Logical conditions:
# 0. If not already in virtualenv:
# 0.1. If virtualenv already exists activate it,
# 0.2. If not create it with global packages, update pip then activate it
# 1. If already in virtualenv: just give info
#
# Usage:
# Without arguments it will create virtualenv named `.venv_vscode_antimony_virtual_env` with `python3.9` version
# $ ve
# or for a specific python version
# $ ve python3.9
# or for a specific python version and environment name;
# $ ve python3.9 ./.venv-diff

ve() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        local py=${1:-python3.9}
        local venv="${2:-./.venv}_vscode_antimony_virtual_env"

        local bin="${venv}/bin/activate"

        echo "running install virtual env"
        # If not already in virtualenv
        # $VIRTUAL_ENV is being set from $venv/bin/activate script
        if [ -z "${VIRTUAL_ENV}" ]; then
            if [ ! -d ${venv} ]; then
                echo "Creating and activating virtual environment ${venv}"
                ${py} -m venv env ${venv} --system-site-package
                echo "export PYTHON=${py}" >> ${bin}    # overwrite ${python} on .zshenv
                source ${bin}
                echo "Upgrading pip"
                ${py} -m pip install --upgrade pip
                python3 -m pip --disable-pip-version-check install -t ./pythonFiles/lib/python \
                    --no-cache-dir --upgrade -r ./all-requirements.txt && success=1
            else
                echo "Virtual environment ${venv} already exists, activating..."            
                source ${bin}
            fi
        else
            echo "Already in a virtual environment!"
        fi
    elif [[ "$OSTYPE" == "win64" ]]; then
        local py=${1:-python3.9}
        local venv="${2:-./.venv}_vscode_antimony_virtual_env"

        local bin="${venv}/bin/activate"

        echo "running install virtual env"
        # If not already in virtualenv
        # $VIRTUAL_ENV is being set from $venv/bin/activate script
        if [ -z "${VIRTUAL_ENV}" ]; then
            if [ ! -d ${venv} ]; then
                echo "Creating and activating virtual environment ${venv}"
                ${py} -m venv env ${venv} --system-site-package
                echo "export PYTHON=${py}" >> ${bin}    # overwrite ${python} on .zshenv
                source ${bin}
                echo "Upgrading pip"
                ${py} -m pip install --upgrade pip
                python3 -m pip --disable-pip-version-check install -t ./pythonFiles/lib/python \
                    --no-cache-dir --upgrade -r ./all-requirements.txt && success=1
            else
                echo "Virtual environment ${venv} already exists, activating..."            
                source ${bin}
            fi
        else
            echo "Already in a virtual environment!"
        fi
    else
        local py=${1:-python3.9}
        local venv="${2:-./.venv}_vscode_antimony_virtual_env"

        local bin="${venv}/bin/activate"

        echo "running install virtual env"
        # If not already in virtualenv
        # $VIRTUAL_ENV is being set from $venv/bin/activate script
        if [ -z "${VIRTUAL_ENV}" ]; then
            if [ ! -d ${venv} ]; then
                echo "Creating and activating virtual environment ${venv}"
                ${py} -m venv env ${venv} --system-site-package
                echo "export PYTHON=${py}" >> ${bin}    # overwrite ${python} on .zshenv
                source ${bin}
                echo "Upgrading pip"
                ${py} -m pip install --upgrade pip
                python3 -m pip --disable-pip-version-check install -t ./pythonFiles/lib/python \
                    --no-cache-dir --upgrade -r ./all-requirements.txt && success=1
            else
                echo "Virtual environment ${venv} already exists, activating..."            
                source ${bin}
            fi
        else
            echo "Already in a virtual environment!"
        fi
    fi
}

ve "$@"