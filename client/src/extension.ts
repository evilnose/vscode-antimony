import { privateEncrypt } from 'crypto';
import * as path from 'path';
import {
	ExtensionContext, commands, SnippetString, window, Range, Position, DecorationOptions, workspace, Event, TextDocument, ColorThemeKind,
} from 'vscode';

import {
	LanguageClient,
	LanguageClientOptions,
	ServerOptions,
	TransportKind
} from 'vscode-languageclient/node';
import { multiStepInput } from './annotationInput';

let client: LanguageClient;

export async function activate(context: ExtensionContext) {
	// TODO allow the user to manually specify an interpreter to use, possibly leveraging the
	// Python language extension. See https://code.visualstudio.com/api/references/vscode-api#extensions
	// TODO this might be python3
	const pythonInterp = 'python';

	const pythonMain = context.asAbsolutePath(
		path.join('server', 'main.py')
	);

	const args = [pythonMain];

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
		commands.registerCommand('antimony.createAnnotationDialog',
			(...args: any[]) => createAnnotationDialog(context, args)));

	// Start the client. This will also launch the server
	client.start();

	decorateDocument(window.activeTextEditor.document);
	workspace.onDidSaveTextDocument(decorateDocument);
	workspace.onDidOpenTextDocument(decorateDocument);
	window.onDidChangeActiveTextEditor(e => decorateDocument(e.document));
	window.onDidChangeActiveColorTheme(() => decorateDocument(window.activeTextEditor.document));
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

async function decorateDocument(doc: TextDocument) {
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
