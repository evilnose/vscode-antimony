/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License. See License.txt in the project root for license information.
 * ------------------------------------------------------------------------------------------ */
import * as vscode from 'vscode';
import * as assert from 'assert';
import { getDocUri, activate } from './helper';

suite('Should do completion', () => {
	// TODO these tests are very far from complete, mainly because completion itself is very far
	// from complete. More tests should be introduced as the parser becomes more complete and better
	// completion is implemented.
	const basicUri = getDocUri('completion/basic.ant');
	const moreUri = getDocUri('completion/more.ant')

	test('Completes basic file', async () => {
		await testCompletion(basicUri, new vscode.Position(2, 0), {
			items: [
				{ label: 'example', kind: vscode.CompletionItemKind.Text },
				{ label: 'example1', kind: vscode.CompletionItemKind.Text },
			]
		});
	});

	test('Completes more complex file', async () => {
		await testCompletion(moreUri, new vscode.Position(7, 0), {
			items: [
				{ label: 'apple_1', kind: vscode.CompletionItemKind.Text },
				{ label: 'apple_2', kind: vscode.CompletionItemKind.Text },
				{ label: 'badfruit', kind: vscode.CompletionItemKind.Text },
				{ label: 'banana', kind: vscode.CompletionItemKind.Text },
				{ label: 'i122', kind: vscode.CompletionItemKind.Text },
				{ label: 'k', kind: vscode.CompletionItemKind.Text },
				{ label: 'orange', kind: vscode.CompletionItemKind.Text },
				{ label: 'peach', kind: vscode.CompletionItemKind.Text },
				{ label: 'watermelon', kind: vscode.CompletionItemKind.Text },
			]
		});
	})
});

async function testCompletion(
	docUri: vscode.Uri,
	position: vscode.Position,
	expectedCompletionList: vscode.CompletionList
) {
	await activate(docUri);

	// Executing the command `vscode.executeCompletionItemProvider` to simulate triggering completion
	const actualCompletionList = (await vscode.commands.executeCommand(
		'vscode.executeCompletionItemProvider',
		docUri,
		position
	)) as vscode.CompletionList;

	const strippedActualList = actualCompletionList.items.map((item) => {
		return {
			label: item.label,
			kind: item.kind
		}
	});

	assert.deepStrictEqual(strippedActualList, expectedCompletionList.items);
}
