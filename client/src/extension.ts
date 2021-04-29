import { privateEncrypt } from 'crypto';
import * as path from 'path';
import {
	workspace, ExtensionContext, commands, InputBoxOptions, window, QuickInputButtons,
	QuickPickItem,
	Position
} from 'vscode';

import {
	LanguageClient,
	LanguageClientOptions,
	ServerOptions,
	TransportKind
} from 'vscode-languageclient/node';
import { multiStepInput } from './annotationInput';

let client: LanguageClient;

export function activate(context: ExtensionContext) {
	// TODO allow the user to manually specify an interpreter to use, possibly leveraging the
	// Python language extension. See https://code.visualstudio.com/api/references/vscode-api#extensions
	// TODO this might be python3
	const pythonInterp = 'python';

	// const pythonMain = context.asAbsolutePath(
	// 	path.join('server', 'main.py')
	// );

	const args = ["-m", "server.main"];

	// Add debug options here if needed
	const serverOptions: ServerOptions = { command: pythonInterp, args };

	const clientOptions: LanguageClientOptions = {
		documentSelector: [
			{ scheme: "file", language: "antimony" },
		],
	};

	// Create the language client and start the client.
	client = new LanguageClient(
		'AntimonyLanguage',
		'Antimony Language Server',
		serverOptions,
		clientOptions
	);

	context.subscriptions.push(
		commands.registerCommand('antimony.createAnnotationDialog', () => createAnnotationDialog(context)));

	// Start the client. This will also launch the server
	client.start();
}

export function deactivate(): Thenable<void> | undefined {
	if (!client) {
		return undefined;
	}
	return client.stop();
}

async function createAnnotationDialog(context) {
	// Wait till client is ready, or the Python server might not have started yet.
	// NOTE this is necessary for any command that might use the Python language server.
	await client.onReady();

	const selection = window.activeTextEditor.selection
	const selectedText = window.activeTextEditor.document.getText(selection);

	const selectedItem = await multiStepInput(context);

	const entity = selectedItem.entity;
	const id = entity['id'];
	const prefix = entity['prefix'];
	const snippet = `\n${selectedText} identity "http://identifiers.org/${prefix}/${id}"\n`;
	window.activeTextEditor.edit((builder) => {
		const doc = window.activeTextEditor.document;
		const pos = doc.lineAt(doc.lineCount - 1).range.end;
		builder.insert(pos, snippet);
	});
}
