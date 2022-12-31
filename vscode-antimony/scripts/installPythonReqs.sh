#!/bin/sh
# Logical conditions:
# 0. If not already in virtualenv:
# 0.1. If virtualenv already exists activate it,
# 0.2. If not create it with global packages, update pip then activate it
# 1. If already in virtualenv: just give info
#
# Usage:
# Without arguments it will create virtualenv named `.venv` with `python3.8` version
# $ ve
# or for a specific python version
# $ ve python3.9
# or for a specific python version and environment name;
# $ ve python3.9 ./.venv-diff
ve() {
    local py=${1:-python3.9}
    local venv="${2:-./.venv}"

    local bin="${venv}/bin/activate"

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
        else
            echo "Virtual environment ${venv} already exists, activating..."
            source ${bin}
        fi
    else
        echo "Already in a virtual environment!"
    fi
}


# set success=0

# # rm -rf ./pythonFiles/lib/python

# python3 -m pip --disable-pip-version-check install -t ./pythonFiles/lib/python \
#     --no-cache-dir --upgrade -r ./all-requirements.txt && success=1

# python -m pip --disable-pip-version-check install -t ./pythonFiles/lib/python --no-cache-dir --upgrade -r ./all-requirements.txt && success=1

# echo "Python libs installed successfully"

# if ((success == 0)); then
#     echo "Failed to install Python libs with 'python3'; now trying 'python'..."
#     python -m pip --disable-pip-version-check install -t ./pythonFiles/lib/python \
#         --no-cache-dir --upgrade -r ./all-requirements.txt && success=1
    
#     if ((success == 0)); then
#         echo "Failed to install Python libs with 'python'."
#     fi
# fi