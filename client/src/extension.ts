import { privateEncrypt } from 'crypto';
import * as path from 'path';
import { workspace, ExtensionContext, commands, InputBoxOptions, window, QuickInputButtons,
	QuickPickItem,
	Position
 } from 'vscode';

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
	
	context.subscriptions.push(
		commands.registerCommand('antimony.createAnnotationDialog', createAnnotationDialog));

	// Start the client. This will also launch the server
	client.start();
}

export function deactivate(): Thenable<void> | undefined {
	if (!client) {
		return undefined;
	}
	return client.stop();
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function createAnnotationDialog() {
	/* */
	const selection = window.activeTextEditor.selection
	const selected = window.activeTextEditor.document.getText(selection);
	let latestChangeIndex = 0;
	let quickPick = window.createQuickPick();
	quickPick.canSelectMany = false;

	quickPick.value = selected;
	let results: Array<unknown> = await commands.executeCommand('antimony.querySpecies', selected);
	// update items
	quickPick.items = results.map((item) => {
		return {
			label: item['name'],
			alwaysShow: true,
		};
	});

	quickPick.onDidChangeValue(async (newValue: string) => {
		// TODO ask extension for a list of items
		// TODO fix bug: try entering "glocu" for annotation
		latestChangeIndex++;
		let myIndex = latestChangeIndex;

		// Our SOAP client is blocking, so we want to avoid sending too many unnecessary requests
		// in a row. Therefore we wait half a sec here to see if the user types more. If they do,
		// then we don't do anything in this handler.
		// It isn't trivial to do non-blocking requests with our existing libraries (suds),
		// especially with the deployment constraints of the VSCode extension. But for now this is
		// fast enough. If we decide to implement non-blocking SOAP requests, see:
		// https://stackoverflow.com/questions/19569701/benefits-of-twisted-suds-async-way-of-using-python-suds-soap-lib
		// Additionally an async HTTP requests library needs to be installed (vanilla requests
		// does not support this), and code in bioservices needs to be rewritten.
		await sleep(250);
		if (latestChangeIndex != myIndex) return;

		let results: Array<unknown> = await commands.executeCommand('antimony.querySpecies', newValue);

		if (latestChangeIndex != myIndex) return;

		// update items
		quickPick.items = results.map((item) => {
			return {
				label: item['name'],
				alwaysShow: true,
				chebiId: item['id'],
			};
		});
	});

	quickPick.onDidChangeSelection(async (items: QuickPickItem[]) => {
		const selectedItem = items[0];
		const chebiId = selectedItem['chebiId'];
		const varText = selected;
		const snippet = `\n${varText} identity "http://identifiers.org/chebi/${chebiId}"\n`;

		window.activeTextEditor.edit((builder) => {
			const doc = window.activeTextEditor.document;
			const pos = doc.lineAt(doc.lineCount - 1).range.end;
			builder.insert(pos, snippet);
			quickPick.dispose();
		});
	});
	quickPick.show();
}
