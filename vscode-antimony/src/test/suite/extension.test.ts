import * as assert from 'assert';

// You can import and use all API from the 'vscode' module
// as well as import your extension to test it
import * as vscode from 'vscode';
// import * as myExtension from '../../extension';

suite('Extension Test Suite', () => {
	vscode.window.showInformationMessage('Start all tests.');

    // Testing VSCode User Settings Switch Indication On
    test("Testing VSCode User Settings Switch Indication On", async () => {
        let settings = vscode.workspace.getConfiguration('vscode-antimony');
        await settings.update("switchIndicationOnOrOff", true, true);
        
        if (vscode.workspace.getConfiguration('vscode-antimony').get("switchIndicationOnOrOff") === true) {
            assert(true);
        } else {
            assert(false);
        }
    });
    
    // Testing VSCode User Settings Switch Indication Off
    test("Testing VSCode User Settings Switch Indication Off", async () => {
        let settings = vscode.workspace.getConfiguration('vscode-antimony');
        await settings.update("switchIndicationOnOrOff", false, true);
        
        if (vscode.workspace.getConfiguration('vscode-antimony').get("switchIndicationOnOrOff") === false) {
            assert(true);
        } else {
            assert(false);
        }
    });

    // Testing VSCode Context Menu Switch On and Setting Syncing
    test("Testing VSCode Context Menu Switch On and Both Settings Syncing", async (done) => {
        if (vscode.workspace.getConfiguration('vscode-antimony').get("switchIndicationOnOrOff") === false) {
            vscode.commands.executeCommand('vscode.antimony.switchIndicationOn');
        }

        done();

        if (vscode.workspace.getConfiguration('vscode-antimony').get("switchIndicationOnOrOff") === true) {
            assert(true);
        } else {
            assert(false);
        }
    });

    // Testing VSCode Context Menu Switch Off and Both Settings Syncing
    test("Testing VSCode Context Menu Switch Off and Both Settings Syncing", async () => {
        if (vscode.workspace.getConfiguration('vscode-antimony').get("switchIndicationOnOrOff") === true) {
            await vscode.commands.executeCommand('antimony.switchIndicationOff');
        }
        
        if (vscode.workspace.getConfiguration('vscode-antimony').get("switchIndicationOnOrOff") === false) {
            assert(true);
        } else {
            assert(false);
        }
    });
});


