# Antimony for Visual Studio Code

[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/tterb/atomic-design-ui/blob/master/LICENSEs)

#### [Repository](https://github.com/sys-bio/vscode-antimony/tree/master/vscode-antimony)&nbsp;&nbsp;|&nbsp;&nbsp;[Issues](https://github.com/sys-bio/vscode-antimony/issues)&nbsp;&nbsp;|&nbsp;&nbsp;[Code Examples](https://github.com/sys-bio/vscode-antimony/tree/master/examples)&nbsp;&nbsp;|&nbsp;&nbsp;[Antimony Reference](https://tellurium.readthedocs.io/en/latest/antimony.html)&nbsp;&nbsp;|&nbsp;&nbsp;[tellurium](https://tellurium.readthedocs.io/en/latest/index.html)&nbsp;&nbsp;|&nbsp;&nbsp;[Marketplace Link](https://github.com/microsoft/vscode-cpptools/releases)&nbsp;&nbsp;|&nbsp;&nbsp;[Marketplace Link for Extension Pack](https://marketplace.visualstudio.com/items?itemName=stevem.antimony-extension-pack)

The Antimony extension adds language support for Antimony to Visual Studio Code for building models in Systems Biology.

The currently available version 0.1 is a public beta version developed by [Gary Geng](https://www.linkedin.com/in/gary-geng-9995a2160/), [Steve Ma](https://www.linkedin.com/in/steve-ma/), and Dr. [Joseph Hellerstein](https://sites.google.com/uw.edu/joseph-hellerstein/home?authuser=0) at the University of Washington. Steve Ma is responsible for future releases, and please feel free to [contact](mailto:bochenma@cs.washington.edu) him if you have any questions.

Please note that the current release does not support the complete Antimony grammar. While most grammar has been supported, more will be included in future releases.

## Features
The extension provides many convenient features for developing biological models with the Antimony language in tellurium. The current release focuses on the areas below.

### 1. Syntax recognition and highlights.

<p align=center>
<img src="docs/images/syntax_highlights.png" width=75%>
<br/>
<em>(Syntax Highlights)</em>
</p>

⚠️ Note: the default syntax highlighting for Antimony is provided by a separate extension [Antimony Syntax](https://marketplace.visualstudio.com/items?itemName=stevem.vscode-antimony-syntax), and is also available in the [Antimony Extension Pack](https://marketplace.visualstudio.com/items?itemName=stevem.antimony-extension-pack) 

### 2. Automatic annotation creation with ChEBI and UniProt

<p align=center>
<img src="docs/images/annotations.gif" width=75%>
<br/>
<em>(Creating an annotation through the ChEBI database)</em>
</p>

⚠️ Note: support for more databases & performance optimization will come soon!

### 3. Hover messages 

<p align=center>
<img src="docs/images/hover.gif" width=75%>
<br/>
<em>(Hovering over species to look up information)</em>
</p>

### 4. Code navigation

<p align=center>
<img src="docs/images/nav.gif" width=75%>
<br/>
<em>(Navigating to the definition code)</em>
</p>

### 5. Error detection
The extension supports various warning and error detections to help modelers debug their model during development. Our design principle for whether an issue should be a warning or an error entirely depends on the logic of tellurium. Our extension will mark the subject as an error if tellurium throws an error while rendering the model, with a red underline. An example would be calling a function that does not exist (usually due to a typo, which is extremely common during development. Read more in my [thesis](https://drive.google.com/file/d/1FutuOYgq9Jd_AHqp_z4f2joDavVIURuz/view?usp=sharing)).

<p align=center>
<img src="docs/images/function.gif" width=75%>
<br/>
<em>(Typos are extremely common in software development)</em>
</p>

On the other hand, certain issues are not errors in tellurium, but we thought it would be worthwhile to have the user's attention. For example, missing initial values for species and overriding a previously defined value.

<p align=center>
<img src="docs/images/warning.gif" width=75%>
<br/>
<em>(Forgetting to initialize the value for a species, causing tellurium to assume a default value)</em>
</p>

The extension supports a wide range of errors and warnings, and we plan to support more in the upcoming releases. Read more in [issues](https://github.com/sys-bio/vscode-antimony/issues).

## Requirements

## Extension Settings

## Known Issues

## Release Notes

### 1.0.0