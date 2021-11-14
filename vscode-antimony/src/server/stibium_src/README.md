# Stibium - Language Support Library for Antimony
This is a language support library for [Antimony](https://tellurium.readthedocs.io/en/latest/antimony.html)
that supports parsing, static analysis, completion, and more.
Stibium provides an simple Python API for performing the above tasks and handling the parse tree.
[Lark](https://github.com/lark-parser/lark) is used as the parser backend.

Stibium requires Python 3.6+.

## Features
* Parse Antimony source files and generate a navigable tree.
* Error recovery during parse.
* Diagnostics: obtain syntax and semantic errors
* Obtain definition of a name (symbol).
* Obtain the name (symbol) at the provided cursor location.
* Autocomplete reaction rate law (e.g. mass-action)
* Basic autocompletion of species names

## Planned Features
* Extend the syntax to parse compartments, events, and models
* Parser Caching
* Better context-sensitive autocompletion, possibly based on the word fragment (prefix) before the
cursor. The current autocompletion is generally pretty dumb -- with the exception of rate law
completion, Stibium does not check for things like scope, keywords, or the context in general.

## Building
* Install the dependencies from `requirements.txt`.
* `python setup.py sdist` to build the package for distribution.

## Testing
* `pytest` is required for testing. Install it from `dev-requirements.txt`.
* `pytest test` to run all the tests.

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
