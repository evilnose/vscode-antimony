import * as vscode from 'vscode';
import * as cp from "child_process";

let debug = vscode.window.createOutputChannel("Debug1");
debug.show();

// util function for showing python interpreter error message
export async function pythonInterpreterError() {
    const choice = await vscode.window.showErrorMessage(
        'Language server not running. Select a valid Python interpreter',
        'Edit in settings');
    if (choice === 'Edit in settings') {
        await vscode.commands.executeCommand('workbench.action.openSettings', 'vscode-antimony.pythonInterpreter');
    }
}

// convert cp.exec to a promise
export function execPromise(command: string) {
    return new Promise(function (resolve, reject) {
        cp.exec(command, (err, stdout, stderr) => {
            if (err) {
                debug.append(err.toString());
                reject(err);
            } else {
                resolve({
                    stdout,
                    stderr,
                });
            }
        })
    });
}