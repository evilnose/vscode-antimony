import * as assert from 'assert';

// You can import and use all API from the 'vscode' module
// as well as import your extension to test it
import * as vscode from 'vscode';
// import * as myExtension from '../../extension';

suite('Extension Test Suite', () => {
	vscode.window.showInformationMessage('Start all tests.');

	test('Sample test', () => {
		assert.strictEqual(-1, [1, 2, 3].indexOf(5));
		assert.strictEqual(-1, [1, 2, 3].indexOf(0));
	});

    test("LoadConfiguration - Shows error when configuration can't be loaded", async () => {
        let settings = vscode.workspace.getConfiguration('vscode-antimony');
        await settings.update("switchIndicationOnOrOff", true);
    
        // await ConfigurationLoader.LoadConfiguration()
    
        if (vscode.workspace.getConfiguration('vscode-antimony').get("switchIndicationOnOrOff") === true) {
            assert(true);
        } else {
            assert(false);
        }
    });
    
    test("LoadConfiguration - Shows error when configuration can't be loaded", async () => {
        let settings = vscode.workspace.getConfiguration('vscode-antimony');
        await settings.update("switchIndicationOnOrOff", false);
    
        // await ConfigurationLoader.LoadConfiguration()
    
        if (vscode.workspace.getConfiguration('vscode-antimony').get("switchIndicationOnOrOff") === false) {
            assert(true);
        } else {
            assert(false);
        }
    });
});


