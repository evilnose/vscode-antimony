"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = require("vscode");
const utils = require("./utils/utils");
const path = require("path");
// for debugging
let debug = vscode.window.createOutputChannel("Debug");
debug.show();
let client = null;
let pythonInterpreter = null;
function activate(context) {
    // start the language server
    startLanguageServer(context);
    // create annotations
    context.subscriptions.push(vscode.commands.registerCommand('antimony.createAnnotationDialog', (...args) => createAnnotationDialog(context, args)));
}
exports.activate = activate;
async function createAnnotationDialog(context, args) {
    // wait till client is ready, or the Python server might not have started yet.
    // note: this is necessary for any command that might use the Python language server.
    if (!client) {
        utils.pythonInterpreterError();
        return;
    }
    await client.onReady();
}
function deactivate() {
    if (!client) {
        return undefined;
    }
    return client.stop();
}
exports.deactivate = deactivate;
// ****** helper functions ******
// starting language server
async function startLanguageServer(context) {
    pythonInterpreter = getPythonInterpreter();
    // verify the interpreter
    const error = await verifyInterpreter(pythonInterpreter);
    if (error !== 0) {
        let errMessage;
        if (error === 1) {
            errMessage = `Failed to launch language server: "${pythonInterpreter}" is not Python 3.7+`;
        }
        else {
            errMessage = `Failed to launch language server: Unable to run "${pythonInterpreter}"`;
        }
        const choice = await vscode.window.showErrorMessage(errMessage, 'Edit in settings');
        if (choice === 'Edit in settings') {
            await vscode.commands.executeCommand('workbench.action.openSettings', 'vscode-antimony.pythonInterpreter');
        }
        return;
    }
    // create language client and launch server
    const pythonMain = context.asAbsolutePath(path.join('server', 'main.py'));
    debug.append(pythonMain);
}
// getting python interpretor
function getPythonInterpreter() {
    const config = vscode.workspace.getConfiguration('vscode-antimony');
    return config.get('pythonInterpreter');
}
// verify python interpeter
async function verifyInterpreter(path) {
    try {
        const result = await utils.execPromise(`"${path}" -c "import sys; print(sys.version_info >= (3, 7))"`);
        if (result['stdout'].trim() === 'True') {
            return 0;
        }
        return 1;
    }
    catch (e) {
        return 2;
    }
}
//# sourceMappingURL=extension.js.map