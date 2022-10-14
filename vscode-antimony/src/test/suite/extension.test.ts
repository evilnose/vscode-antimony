import * as assert from 'assert';

// You can import and use all API from the 'vscode' module
// as well as import your extension to test it
import * as vscode from 'vscode';
// import * as myExtension from '../../extension';

suite('Extension Test Suite', () => {
	vscode.window.showInformationMessage('Start all tests.');

	// Testing VSCode Response of Rate Law Button in Context Menu
	test("Testing VSCode Rate Law Context Menu Button Response", async () => {
        await vscode.commands.executeCommand('antimony.insertRateLawDialog');
        if (console.error() == null){
            assert(true);
        } else {
            assert(false);
        }
    });

	// 
	// 



});
