import * as path from 'path';
import { workspace, ExtensionContext } from 'vscode';

import {
	LanguageClient,
	LanguageClientOptions,
	ServerOptions,
	TransportKind
} from 'vscode-languageclient/node';

let client: LanguageClient;

export function activate(context: ExtensionContext) {
	// TODO allow the user to manually specify an interpreter to use, possibly leveraging the
	// Python language extension. See https://code.visualstudio.com/api/references/vscode-api#extensions
	const pythonInterp = 'python';

	const pythonMain = context.asAbsolutePath(
		path.join('server', 'main.py')
	);

	const args = [pythonMain];

	// Add debug options here if needed
	const serverOptions: ServerOptions = { command: pythonInterp, args };

	const clientOptions: LanguageClientOptions = {
		documentSelector: [{ scheme: 'file', language: 'plaintext' }],
	};

	// Create the language client and start the client.
	client = new LanguageClient(
		'AntimonyLanguage',
		'Antimony Language Server',
		serverOptions,
		clientOptions
	);

	// Start the client. This will also launch the server
	client.start();
}

export function deactivate(): Thenable<void> | undefined {
	if (!client) {
		return undefined;
	}
	return client.stop();
}
