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
* Refactor stibium and the server. Move AntFile to stibium. Reorganize requirements
* Tests! Need to have em. Especially need to test error recovery, before I forget
* Multithreading for pygls (especially for querying)
* Figure out the licenses
* Handle cases where Python is not found
* Better annotations UI flow (add "loading" to title when doing requests; more information in
selection items, maybe even use tabular format.)

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
                "script": "test-compile"
            },
            "name": "Extension Tests",
            "type": "extensionHost",
            "request": "launch",
            "runtimeExecutable": "${execPath}",
            "args": [
                "--extensionDevelopmentPath=${workspaceFolder}",
                "--extensionTestsPath=${workspaceFolder}/client/out/test/index",
                "--disable-extensions"
            ],
            "outFiles": [
                "${workspaceFolder}/out/test/**/*.js"
            ],
            // This is required so that the test output can be shown. For some reason this is
            // not the default
            "internalConsoleOptions": "openOnSessionStart"
        }
    ]
}
```
This way you can directly run the test from within VSCode.


## Test TODOs
* completion
* diagnostics (warnings & errors)
* annotations
* parser
* parser error recovery
* symbol_at
* resolve_qname
