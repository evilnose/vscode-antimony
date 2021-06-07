import { execPromise } from './utils';
import * as path from 'path';
import {
	ExtensionContext, commands, SnippetString, window, Range, Position, DecorationOptions, workspace, Event, TextDocument, ColorThemeKind, Disposable, EnvironmentVariableMutatorType, languages, CodeLensProvider, CodeLens, Command, Uri,
} from 'vscode';

import {
	LanguageClient,
	LanguageClientOptions,
	ServerOptions,
	TransportKind
} from 'vscode-languageclient/node';
import { multiStepInput } from './annotationInput';

let client: LanguageClient = null;
let curPythonInterp: string | null = null;
let lastChangeInterp = 0;


class AntCodeLensProvider implements CodeLensProvider {
	async provideCodeLenses(document: TextDocument): Promise<CodeLens[]> {
		if (document.languageId === 'antimony' && !document.getText().trim()) {
			const topOfDocument = new Range(0, 0, 0, 0);

			let c: Command = {
				title: 'BioIDE Help Page',
				command: 'vscode.open',
				arguments: [Uri.parse('https://github.com/evilnose/vscode-antimony#usage')],
			}
			let codeLens = new CodeLens(topOfDocument, c)
			return [codeLens];
		}

		return [];
	}
}

// HACK returns 0 if fine, 1 if Python version is too low, or 2 if the process failed.
async function verifyPythonInterp(path: string) {
	try {
		const result = await execPromise(`"${path}" -c "import sys; print(sys.version_info >= (3, 6))"`);
		if (result['stdout'].trim() === 'True') {
			return 0;
		}
		return 1;
	} catch (e) {
		return 2;
	}
}

function getPythonInterpSetting(): string {
	const config = workspace.getConfiguration('bio-ide');
	return config.get('pythonInterpreter');
}

// start the language server client
async function startLSClient(context: ExtensionContext) {
	curPythonInterp = getPythonInterpSetting();

	const error = await verifyPythonInterp(curPythonInterp);
	if (error !== 0) {
		let errMessage: string;
		if (error === 1) {
			errMessage = `Failed to launch language server: "${curPythonInterp}" is not Python 3.6+`;
		} else {
			errMessage = `Failed to launch language server: Unable to run "${curPythonInterp}"`;
		}
		const choice = await window.showErrorMessage(errMessage, 'Edit in settings');
		if (choice === 'Edit in settings') {
			await commands.executeCommand('workbench.action.openSettings', 'bio-ide.pythonInterpreter');
		}
		return;
	}

	const pythonMain = context.asAbsolutePath(
		path.join('server', 'main.py')
	);

	const args = [pythonMain];

	// Add debug options here if needed
	const serverOptions: ServerOptions = { command: curPythonInterp, args };

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

	// Start the client. This will also launch the server
	const clientDisposable = client.start();
	context.subscriptions.push(clientDisposable);
}

export async function activate(context: ExtensionContext) {
	// TODO allow the user to manually specify an interpreter to use, possibly leveraging the
	// Python language extension. See https://code.visualstudio.com/api/references/vscode-api#extensions
	// TODO this might be python3
	startLSClient(context);

	context.subscriptions.push(
		commands.registerCommand('antimony.createAnnotationDialog',
			(...args: any[]) => createAnnotationDialog(context, args)));

	decorateDocument(window.activeTextEditor?.document);
	workspace.onDidChangeConfiguration(async (e) => {
		if (!e.affectsConfiguration('bio-ide')) {
			return;
		}
		let curTime = Date.now();
		lastChangeInterp = curTime;
		// delay restarting the client by 3 seconds. i.e. if any other changes were made in 3
		// seconds, then don't do the earlier change
		setTimeout(async () => {
			if (curTime !== lastChangeInterp) {
				return;
			}
			// python interpreter changed. restart language client
			if (client) {
				client.stop();
				client = null;
			}
			await startLSClient(context);
		}, 3000);
	})
	const docSelector = {
		language: 'antimony',
		scheme: 'file',
	}
	let codeLensProviderDisposable = languages.registerCodeLensProvider(
		docSelector,
		new AntCodeLensProvider()
	)

	context.subscriptions.push(codeLensProviderDisposable)
	workspace.onDidSaveTextDocument(decorateDocument);
	workspace.onDidOpenTextDocument((doc: TextDocument) => {
		decorateDocument(doc);
	});
	window.onDidChangeActiveTextEditor(async e => {
		decorateDocument(e?.document)
	});
	window.onDidChangeActiveColorTheme(() => decorateDocument(window.activeTextEditor?.document));
}

export function deactivate(): Thenable<void> | undefined {
	if (!client) {
		return undefined;
	}
	return client.stop();
}

// initialEntity is for testing and debugging. When executed in production, it is always null
async function createAnnotationDialog(context, args: any[]) {
	// Wait till client is ready, or the Python server might not have started yet.
	// NOTE this is necessary for any command that might use the Python language server.
	if (!client) {
		// TODO show error message
		const choice = await window.showErrorMessage(
			'Language server not running. Select a valid Python interpreter',
			'Edit in settings');
		if (choice === 'Edit in settings') {
			await commands.executeCommand('workbench.action.openSettings', 'bio-ide.pythonInterpreter');
		}
		return;
	}
	await client.onReady();

	const selection = window.activeTextEditor.selection
	const selectedText = window.activeTextEditor.document.getText(selection);
	const initialEntity = selectedText || 'entityName';

	let initialQuery;
	if (args.length == 2) {
		initialQuery = args[1];
	} else {
		initialQuery = selectedText;
	}

	const selectedItem = await multiStepInput(context, initialQuery);

	await insertAnnotation(selectedItem, initialEntity);
}

async function insertAnnotation(selectedItem, entityName) {
	const entity = selectedItem.entity;
	const id = entity['id'];
	const prefix = entity['prefix'];
	const snippetText = `\n\${1:${entityName}} identity "http://identifiers.org/${prefix}/${id}"\n`;
	const snippetStr = new SnippetString(snippetText);

	const doc = window.activeTextEditor.document;
	const pos = doc.lineAt(doc.lineCount - 1).range.end;
	window.activeTextEditor.insertSnippet(snippetStr, pos);
}

interface ServerRange {
	line: number;
	column: number;
	end_line: number;
	end_column: number;
}
const annotDecorTypeDark = window.createTextEditorDecorationType({
	borderStyle: 'none none solid none',
	borderColor: 'white',
	borderWidth: '1px',
});
const annotDecorTypeLight = window.createTextEditorDecorationType({
	borderStyle: 'none none solid none',
	borderColor: 'black',
	borderWidth: '1px',
});

async function decorateDocument(doc: TextDocument | undefined) {
	if (!doc || !client) {
		return;
	}
	await client.onReady();
	if (doc.languageId !== 'antimony') {
		return;
	}

	let decorations: DecorationOptions[] = [];
	const sranges: ServerRange[] = await commands.executeCommand('antimony.getAnnotated', doc.getText());

	for (const srange of sranges) {
		const range = new Range(
			new Position(srange.line, srange.column),
			new Position(srange.end_line, srange.end_column),
		);

		const decor = { range };
		decorations.push(decor);
	}

	const isLight = window.activeColorTheme.kind === ColorThemeKind.Light;
	const decorType = isLight ? annotDecorTypeLight : annotDecorTypeDark;
	const otherDecorType = !isLight ? annotDecorTypeLight : annotDecorTypeDark;
	window.activeTextEditor.setDecorations(decorType, decorations);
	window.activeTextEditor.setDecorations(otherDecorType, []);
}
