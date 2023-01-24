@echo off

echo "script runs"

:ve
setlocal
set py=%1
if "%py%"=="" set py=python3.9
set venv=venv_vscode_antimony_virtual_env
set bin=%venv%\Scripts\activate.bat

echo "running install virtual env"

rem If not already in virtualenv
rem %VIRTUAL_ENV% is being set from %venv%\Scripts\activate.bat script
if "%VIRTUAL_ENV%"=="" (
    if not exist %venv% (
        echo Creating and activating virtual environment %venv%
        py -m venv %venv% --system-site-package
        echo set "PYTHON=%py%" >> %bin%
        call %bin%
        echo Upgrading pip
        py -m pip install --upgrade pip
        py -m pip --disable-pip-version-check install -t ./pythonFiles/lib/python --no-cache-dir --upgrade -r ./all-requirements.txt
    ) else (
        echo Virtual environment %venv% already exists, activating...
        call %bin%
    )
) else (
    echo Already in a virtual environment!
)

ve %*
