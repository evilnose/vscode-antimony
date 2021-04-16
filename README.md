# BioIDEK README WIP

## Current Features
* Basic autocompletion of species names
* Recovery from syntax error

## Planned Features
* Syntax highlighting
* Parser Caching
* Annotations
* Parse more complex syntaxes, including compartments, events, and models
* Autocompletion based on cursor position (context)

## TODOs
* Tests! Need to have em
* Multithreading for pygls (especially for querying)
* Figure out the licenses
* Error handling: what if there is no internet? no python? See message here
```
Traceback (most recent call last):
  File "c:\Users\Gary\.vscode\extensions\sauro-lab.bio-idek-0.0.1\server\main.py", line 48, in <module>
    from annotation import chebi_search
  File "c:\Users\Gary\.vscode\extensions\sauro-lab.bio-idek-0.0.1\server\annotation.py", line 5, in <module>
    chebi = ChEBI()
  File "c:\Users\Gary\.vscode\extensions\sauro-lab.bio-idek-0.0.1\server\bioservices\chebi.py", line 62, in __init__
    verbose=verbose)
  File "c:\Users\Gary\.vscode\extensions\sauro-lab.bio-idek-0.0.1\server\bioservices\services.py", line 268, in __init__
    raise Exception
```

## How to Run Tests
Run `npm test` directly. However, if you are using VSCode for development this wouldn't work (see
[this](https://code.visualstudio.com/api/working-with-extensions/testing-extension#using-insiders-version-for-extension-development)).
In this case I recommend creating a `launch.json` like so:
```
{
    "version": "0.2.0",
    "configurations": [
        {
            "preLaunchTask": {
                "type": "npm",
                "script": "compile"
            },
            "name": "Extension Tests",
            "type": "extensionHost",
            "request": "launch",
            "runtimeExecutable": "${execPath}",
            "args": [
                "--extensionDevelopmentPath=${workspaceFolder}",
                "--extensionTestsPath=${workspaceFolder}/client/out/test/index"
            ],
            "outFiles": [
                "${workspaceFolder}/out/test/**/*.js"
            ]
        }
    ]
}
```
This way you can directly run the test from within VSCode.
