# BioIDE VSCode Extension
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

## Installing
This extension is still in development and is not yet published in the VSCode Marketplace. To
manually install, first download the release binary
[bio-ide-0.0.1.vsix](https://github.com/evilnose/vscode-antimony/releases/download/v0.0.1-alpha/bio-ide-0.0.1.vsix). Then, to install the
extension:

* Press `ctrl+shift+P` (or `cmd+shift+P` on Mac) to bring up the Command Palette
* Type "vsix" into the text box
* Select the option **Extensions: Install from VSIX**. A file explorer will pop up.
* Select the `.vsix` file that was downloaded.

You can also follow the official instructions for installing a local extension
[here](https://code.visualstudio.com/docs/editor/extension-marketplace#_install-from-a-vsix).

After you've installed it, create an Antimony source file `*.ant` to get started. See [usage](#usage)
for more details.

## Usage
This extension mainly operates on Antimony source files, which are files that end with `.ant`. So
for intellisense, autocompletion, etc. to work, you must have a `.ant` file open.

### Annotations
* Be in an Antimony file.
* Right click to bring up the context menu.
* Select "Create Annotation" to bring up the annotation dialog menu.
* Select the database in which to query, one of "ChEBI" and "UniProt".
* Enter the species query. The available list of selection will update according to what is entered.
* The format of the query is the same as those on the [CheBI](https://www.ebi.ac.uk/chebi/) website
and the [UniProtKB](https://www.uniprot.org/) website.
* Once you have found the desired annotation, click on the selection. A piece of annotation code
will be automatically generated and appended to the end of the file.

You can optionally select the name of a variable beforehand. This will populate the species query
input and the generated annotation code with that name.

After you have generated an annotation, you can save the file, and all appearances of the species
that was annotated would be marked in the document.

### Autocompletion
Autocompletion can be manually triggered by pressing Ctrl + Space.

You can generate reaction mass-action rate laws if the cursor is at the rate law section of the
reaction, e.g.

`J7: Acetyladehyde + NADH -> NAD + $ethanol; `
                                            ^ here

If the rate law completion item is not already selected when the completion is triggered, you can
type "mass action" to filter the completion results. Once the desired completion item is highlighted
press `Enter` to perform the completion.

Autocomplete inserts a code snippet for you, with the option to change the names of the generated
parameter names. You can type in whatever name you want, and then press `tab` to cycle to the next
generated name.

Note that the reversibility of the reaction, namely the use of `->` or `=>` is accounted for. If
you are using `=>`, the reaction will be detected as reversible, and the generated rate law will
reflect that.

### Definitions
Hover over any variable name with your cursor to see its type and, if applicable, its annotation
link.

Click on the name while pressing `ctrl` will bring you to the location where it is declared; if it 
is not explicitly declared, where it is assigned a value; otherwise, its first apperance.

## Planned Features
* Better annotations UI flow (add "loading" to title when doing requests; more information in
selection items, maybe even use tabular format.)
* For language support features, see [Stibium](https://github.com/evilnose/stibium).

## Dev Requirements
Python >= 3.7, `node` & `npm`, andVSCode >= 1.52.0 is required.

## What About Python 3.6?
Making this extension work for Python 3.6 is a bit convoluted due to the usage of the
`dataclass` package. 

When building, we tell `pip` to copy all the local Python dependencies to `pythonFiles`,
which is bundled with the extension. The dependencies are pure Python so they should work with
Python 3.6+ no matter which Python `pip` belongs to. The problem: `dataclass` ships with 
Python 3.7+ but comes as a PyPI package for Python 3.6. Then, if we install `dataclass` into
`pythonFiles`, a Python 3.7+ installation will use that instead of the built-in `dataclass`
package, causing issues. But if we don't install `dataclass`, Python 3.6 doesn't work.

In short, the issue is that Python 3.6 and 3.7+ require different sets of packages.

In the future, if support for Python 3.6 is needed, we can install the `dataclass` package to
a separate directory in `pythonFiles`, and then prepend it to `sys.path` only if we can verify that
the current Python version is 3.6.

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
