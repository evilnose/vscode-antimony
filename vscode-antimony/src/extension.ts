// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';

// For debugging
let debug = vscode.window.createOutputChannel("Debug");
debug.show();

// this method is called when your extension is activated
// your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	context.subscriptions.push(
		vscode.commands.registerCommand('antimony.createAnnotationDialog',
			(...args: any[]) => createAnnotationDialog(context, args)));
}

async function createAnnotationDialog(context: vscode.ExtensionContext, args: any[]) {
	
}

// this method is called when your extension is deactivated
export function deactivate() {}
