import * as vscode from 'vscode';
import * as utils from './utils/utils';
import {
	LanguageClient,
} from 'vscode-languageclient/node';

export class SBMLEditorProvider implements vscode.CustomTextEditorProvider {

    public static async register(context: vscode.ExtensionContext, client: LanguageClient): Promise<vscode.Disposable> {
        if (!client) {
            utils.pythonInterpreterError();
            return;
        }
        await client.onReady();

		const provider = new SBMLEditorProvider(context);
		const providerRegistration = vscode.window.registerCustomEditorProvider(SBMLEditorProvider.viewType, provider);
		return providerRegistration;
	}
    
    private static readonly viewType = 'antimony.sbmlEditor';

    constructor(
		private readonly context: vscode.ExtensionContext
	) { }

    /**
	 * Called when our custom editor is opened.
	 * 
	 * 
	 */
	public async resolveCustomTextEditor(
		document: vscode.TextDocument,
		webviewPanel: vscode.WebviewPanel,
		_token: vscode.CancellationToken
	): Promise<void> {
        // Setup initial content for the webview
		webviewPanel.webview.options = {
			enableScripts: true,
		};
		getSBMLString(document, webviewPanel)

		const changeDocumentSubscription = vscode.workspace.onDidSaveTextDocument(e => {
			if (!webviewPanel.active && e.uri.toString() === document.uri.toString()) {
				getSBMLString(document, webviewPanel)
			}
		});

        webviewPanel.onDidDispose(() => {
			changeDocumentSubscription.dispose();
		});

        webviewPanel.webview.onDidReceiveMessage(
            message => {
                switch (message.command) {
                case 'sbmlOnSave':
                    webviewPanel.webview.html = 
                    `
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>SBML</title>
                    </head>
                    <body>
                        <div contenteditable="true" id="sbml">
                            <pre lang="xml" id="sbml-text">
                                ${message.sbml}
                            </pre>
                            <script>
                                let size = getComputedStyle(document.body).getPropertyValue('--vscode-editor-font-size')
                                document.getElementById("sbml").style="font-size: " + size;
        
                                (function() {
                                    const vscode = acquireVsCodeApi();
                                    document.addEventListener('keydown', e => {
                                        if (e.ctrlKey && e.key === 's') {
                                            const node = document.getElementById('sbml-text');
                                            vscode.postMessage({
                                                command: 'sbmlOnSave',
                                                sbml: node.innerHTML
                                            })
                                        }
                                    });
                                }())
                            </script>
                        </div>
                        
                    </html>
                    `;
                    let msg = String(message.sbml).replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/"/g, '"');
                    vscode.commands.executeCommand('antimony.sbmlStrToAntStr', msg)
                        .then(async (result: any) => {
                            if (result.error) {
                                vscode.window.showErrorMessage(`Error while converting: ${result.error}`)
                            } else {
                                const edit = new vscode.WorkspaceEdit();
                                edit.replace(
                                    document.uri,
                                    new vscode.Range(0, 0, document.lineCount, 0),
                                    result);
                                return vscode.workspace.applyEdit(edit);
                            }
                        })
                }
            });
    }
}

function getSBMLString(document: vscode.TextDocument, webviewPanel: vscode.WebviewPanel): any {
    vscode.commands.executeCommand('antimony.antFileToSBMLStr', document)
    .then(async (result: any) => {
        let msg = '';
        if (result.error) {
            msg = result.error;
            webviewPanel.webview.html = 
                `
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>SBML</title>
                </head>
                <body>
                    <div id="sbml">
                        <p id="sbml-text">
                            ${msg}
                        </p>
                        <script>
                            let size = getComputedStyle(document.body).getPropertyValue('--vscode-editor-font-size')
                            document.getElementById("sbml").style="font-size: " + size;
                        </script>
                    </div>
                    
                </html>
                `;
        }
        else {
            msg = result.sbml_str;
            msg = String(msg).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
            webviewPanel.webview.html = 
                `
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>SBML</title>
                </head>
                <body>
                    <div contenteditable="true" id="sbml">
                        <pre lang="xml" id="sbml-text">
                            ${msg}
                        </pre>
                        <script>
                            let size = getComputedStyle(document.body).getPropertyValue('--vscode-editor-font-size')
                            document.getElementById("sbml").style="font-size: " + size;
    
                            (function() {
                                const vscode = acquireVsCodeApi();
                                document.addEventListener('keydown', e => {
                                    if (e.ctrlKey && e.key === 's') {
                                        const node = document.getElementById('sbml-text');
                                        vscode.postMessage({
                                            command: 'sbmlOnSave',
                                            sbml: node.innerHTML
                                        })
                                    }
                                });
                            }())
                        </script>
                    </div>
                    
                </html>
                `;
        }
    });
}
