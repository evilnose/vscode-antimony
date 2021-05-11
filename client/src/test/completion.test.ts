/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License. See License.txt in the project root for license information.
 * ------------------------------------------------------------------------------------------ */
import * as vscode from 'vscode';
import * as assert from 'assert';
import { getDocUri, activate } from './helper';
import { privateEncrypt } from 'crypto';

suite('Should do completion', () => {
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
				{ label: 'banana', kind: vscode.CompletionItemKind.Text },
				// TODO add this back once we handle annotation statements
				// { label: 'i122', kind: vscode.CompletionItemKind.Text },
				{ label: 'orange', kind: vscode.CompletionItemKind.Text },
				{ label: 'peach', kind: vscode.CompletionItemKind.Text },
				{ label: 'vroom', kind: vscode.CompletionItemKind.Text },
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
	})

	assert.deepStrictEqual(strippedActualList, expectedCompletionList.items)
	// expectedCompletionList.items.forEach((expectedItem, i) => {
	// 	const actualItem = actualCompletionList.items[i];
	// 	assert.strictEqual(actualItem.label, expectedItem.label);
	// 	assert.strictEqual(actualItem.kind, expectedItem.kind);
	// });
}
