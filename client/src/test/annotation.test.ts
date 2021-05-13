import * as vscode from 'vscode';
import * as assert from 'assert';
// import { activate } from '../extension';
import { getDocUri, activate } from './helper';
import { sleep } from '../utils';

suite('Should do annotation', () => {
    const emptyUri = getDocUri('completion/empty.ant');

    teardown(async () => {
        await vscode.commands.executeCommand('workbench.action.closeActiveEditor');
    });

    test('Annotate "glucose" with ChEBI', async () => {
        await testAnnotation(emptyUri, 'chebi', 'glucose', glucoseChEBICallback);
    });

    test('Annotate second query result of "gluc" with ChEBI', async () => {
        await testAnnotation(emptyUri, 'chebi', 'gluc', glucChEBICallback);
    });

    test('Annotate "glucose" with UniProt', async () => {
        await testAnnotation(emptyUri, 'uniprot', 'glucose', glucoseUniProtCallback);
    });

    // TODO test with selected text
});

async function selectNthItem(n: number) {
    for (let i = 0; i < n; i++) {
        await vscode.commands.executeCommand('workbench.action.quickOpenSelectNext');
    }
    await vscode.commands.executeCommand('workbench.action.acceptSelectedQuickOpenItem');
}

// testCallback is called after the database is selected and the entity value is set
// TODO if initialEntity is null, then only pass one argument to createAnnotationDialog
// this way we can test createAnnotationDialog with selected text
async function testAnnotation(docUri, databaseName, initialEntity : string, testCallback) {
    let dbIdx;
    if (databaseName === 'chebi') {
        dbIdx = 0;
    } else if (databaseName === 'uniprot') {
        dbIdx = 1;
    } else {
        assert(false, "unknown database name");
    }

    await activate(docUri);
    // need to pass a null argument at the front, since when createAnnotationDialog is executed
    // from the menu, vscode passes along one argument relating to that menu by default.
    let dialogClosed = false;
    vscode.commands.executeCommand('antimony.createAnnotationDialog', null,
        initialEntity).then(() => {
            dialogClosed = true;
        });

    // select database
    await selectNthItem(dbIdx);

    // right now the quickInput is setting its value and the selections are being updated
    // sleep because query selection updates are asynchronous
    await sleep(3000);

    await testCallback();

    // the dialog should be closed now
    assert(dialogClosed);
}

async function glucoseChEBICallback() {
    // select first query result
    await selectNthItem(0);
    await sleep(1000);

    const expected = '\nentityName identity "http://identifiers.org/chebi/CHEBI:17234"\n';
    // replace carriage returns with \n
    const actual = vscode.window.activeTextEditor.document.getText().replace(/\r/g, '');

    assert.strictEqual(actual, expected);
}

async function glucChEBICallback() {
    // select third query result
    await selectNthItem(2);
    await sleep(1000);

    const regex = new RegExp(
        '^\nentityName identity "http:\/\/identifiers\.org\/chebi\/CHEBI:[0-9]+"\n$');
    // replace carriage returns with \n
    const actual = vscode.window.activeTextEditor.document.getText().replace(/\r/g, '');

    assert(regex.test(actual));
}

async function glucoseUniProtCallback() {
    // select first query result
    await selectNthItem(0);
    await sleep(1000);

    const regex = new RegExp(
        '^\nentityName identity "http:\/\/identifiers\.org\/uniprot\/P([0-9]|[A-Z])+"\n$');
    // replace carriage returns with \n
    const actual = vscode.window.activeTextEditor.document.getText().replace(/\r/g, '');

    assert(regex.test(actual));
}
