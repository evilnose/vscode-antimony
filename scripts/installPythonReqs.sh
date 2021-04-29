#!/usr/bin/env bash

set success=0

python3 -m pip --disable-pip-version-check install -t ./pythonFiles/lib/python \
    --no-cache-dir --implementation py --no-deps --upgrade -r ./all-requirements.txt && success=1
    
if ((success == 0)); then
    echo "Failed to install Python libs with 'python3'; now trying 'python'..."
    python -m pip --disable-pip-version-check install -t ./pythonFiles/lib/python \
        --no-cache-dir --implementation py --no-deps --upgrade -r ./all-requirements.txt && success=1
    
    if ((success == 0)); then
        echo "Failed to install Python libs with 'python'."
    fi
fi
