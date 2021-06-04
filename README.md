# BioIDEK VSCode Extension
This is a VSCode extension for the Antimony language. The backend used for parsing and analyzing 
Antimony is [Stibium](https://github.com/evilnose/stibium).

This tool is still in development stage, and the progress of this extension heavily depends on the
progress of the Stibium project. And as of now, Stibium is capable of handling only a subset of the
language.

The below features are currently supported:
* Syntax highlighting
* Diagnostics: syntax and semantic errors
* Definition: hover over a name to see its type and definition
* Basic autocompletion
* Autocomplete reaction rate law (e.g. mass-action)
* Convenient generation of annotation (see below for more information)

## Planned Features
* Better annotations UI flow (add "loading" to title when doing requests; more information in
selection items, maybe even use tabular format.)
* For language support features, see [Stibium](https://github.com/evilnose/stibium).

## Requirements
Python == 3.6, `node` & `npm`, andVSCode >= 1.52.0 is required.
Why exactly Python 3.6? When building, we tell
`pip` to copy all the local Python dependencies to `pythonFiles`, which is bundled with the
extension. The dependencies are pure Python so they should work with Python 3.6+ no matter which
Python `pip` belongs to. But the package `dataclasses` can only be installed by a Python 3.6 `pip`,
and that's why a local Python 3.6 is needed. As a note, `dataclasses` ships with Python 3.7, but
for Python 3.6 it comes as a PyPI package. For some reason it is not added to `__future__`, but oh
well.

Note that Python 3.6 is required for bundling, but any above 3.6 is fine for local development.
Also note that for now Stibium has not been published as a PyPI package, so the local submodule
is required. In the future, it should be added as a line in `requirements.txt`.

## Building
* If running first time, run `npm install`.
* Run `vsce package` to create a bundled extension `bio-idek-0.0.1.vsix`. Right-click it in
VSCode to install it.

## Running locally
* `pip install -r requirements.txt` first.
* To run a test script at `server/test.py`, do `python -m server.test`.

## Files
Below is a description of the directory structure.
* `client`: The language server client for VSCode. This can be considered the frontend of the
extension, and it interacts with the VSCode API directly.
* `dist`: Folder that holds the JS files compiled from the Typescript source, when running
`vscode package`.
* `pythonFiles`: Contains the Python dependencies for the extension during runtime.
Installed in `installPythonReqs.sh`. The developer installs files here, and the files here are
bundled into the extension during build.
* `scripts`: Used by `package.json` for certain commands. If one Windows, Powershell may be needed.
See `package.json` for which are used.
* `server`: The entry point for the backend language server. Note that the decoupling between this
and `stibium_server_src` is not great right now. Ideally, as much code as possible (without 
breaking compatibility with other IDEs) should be in `stibium_server_src`, and `server` should just
be a driver.
* `server/test.py`: Completely optional and temporary file for quick local testing & inspection.
* `stibium_server_src`: Python implementation of a langauge server for Antimony.
This might be refactored into its own project in the future, if there are plans to create plugins
for other IDEs. As in, this follows the Language Server Protocol and could be reused.
* `stibium_src`: Submodule folder for Stibium. This would be removed in the future when Stibium
is published as a Python package.
* `syntaxes`: Holds TextMate syntax highlight files. They are used for VSCode.
* `all-dependencies.txt`: This holds all the Python dependencies for the extension, as in, even
the dependencies of the dependencies in `requirements.txt`. This is required since we tell `pip`
to only install pure Python packages for bundling, and for that to work, we need to pass to `pip`
every package we need. Therefore, if a new dependency is added to `requirements.txt`,
`all-requirements.txt` should be re-generated using `pip freeze > all-requirements.txt`.
* `language-configuration.json`: See VSCode [docs](https://code.visualstudio.com/api/language-extensions/language-configuration-guide)
for details.
* `package.json`: Used by VScode as a manifest file for the extension. See VSCode docs for more info.
* `webpack.config.js`: Used to compile Typescript files and bundled the extension into one single
minified JS file. See Webpack docs for details.

## TODOs
* Refactor stibium and the server. Move AntFile to stibium. Reorganize requirements
* Figure out the licenses
* Handle cases where Python is not found

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

Also note that `runTestDriver.bat` is invoked. If you are on Mac or Linux, change the file name to
`runTestDriver.sh` in `package.json`. In the future this should be replaced by a cross-platform
script (Python would work great).

## Test TODOs
* symbol_at
* resolve_qname
