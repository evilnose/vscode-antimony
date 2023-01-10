import subprocess
import os
import logging

def main():
    vscode_logger = logging.getLogger("vscode-antimony logger")
    EXTENSION_ROOT = os.path.dirname(os.path.abspath(__file__))
    vscode_logger.info(EXTENSION_ROOT)
    subprocess.run([EXTENSION_ROOT + "/virtualEnvPython.sh"], capture_output=True)

if __file__ == '__main__':
    main()