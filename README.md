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
* Add transformers to change the parse tree into a more friendly structure. E.g. removing 'suite'
nodes, adding different classes such as 'Reaction', 'Assignment', etc. and related methods
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


## Notes on Error Recovery
For now error recovery is based solely on threshold set by `simple_stmt`. Namely, when an error
token is encountered, I backtrack to the last fully parsed `simple_stmt` node as the last valid
state. By inspecting the (LALR) parser stack, all nodes/tokens encountered between the last fully
parsed `simple_stmt` and the error token are formed into an `ErrorNode`, and the errored token is
formed into an `ErrorToken`. The parser state is then set to as if it just finished parsing a
`simple_stmt`.

In the future, when models and functions are introduced, we will need to modify `parse.py` so that
instead of backtracking to the last `simple_stmt`, we instead go to the last full statement/model/
function, whichever rule that is.


## Test TODOs
* completion
* diagnostics (warnings & errors)
* annotations
* parser
* parser error recovery
* symbol_at
* resolve_qname
