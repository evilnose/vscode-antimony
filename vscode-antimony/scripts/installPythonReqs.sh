#!/usr/bin/env bash

set success=0

rm -rf ./pythonFiles/lib/python

python3 -m pip --disable-pip-version-check install -t ./pythonFiles/lib/python \
    --no-cache-dir --upgrade -r ./all-requirements.txt && success=1

echo "Python libs installed successfully"

if ((success == 0)); then
    echo "Failed to install Python libs with 'python3'; now trying 'python'..."
    python -m pip --disable-pip-version-check install -t ./pythonFiles/lib/python \
        --no-cache-dir --upgrade -r ./all-requirements.txt && success=1
    
    if ((success == 0)); then
        echo "Failed to install Python libs with 'python'."
    fi
fi