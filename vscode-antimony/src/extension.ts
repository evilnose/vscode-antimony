import * as vscode from 'vscode';
import {
	LanguageClient,
	LanguageClientOptions,
	ServerOptions,
	TransportKind
} from 'vscode-languageclient/node';

// For debugging
let debug = vscode.window.createOutputChannel("Debug");
debug.show();

export function activate(context: vscode.ExtensionContext) {
	context.subscriptions.push(
		vscode.commands.registerCommand('antimony.createAnnotationDialog',
			(...args: any[]) => createAnnotationDialog(context, args)));
}

async function createAnnotationDialog(context: vscode.ExtensionContext, args: any[]) {
	
}

export function deactivate() {}
