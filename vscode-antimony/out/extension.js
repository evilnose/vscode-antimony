"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = require("vscode");
// For debugging
let debug = vscode.window.createOutputChannel("Debug");
debug.show();
function activate(context) {
    context.subscriptions.push(vscode.commands.registerCommand('antimony.createAnnotationDialog', (...args) => createAnnotationDialog(context, args)));
}
exports.activate = activate;
async function createAnnotationDialog(context, args) {
    debug.append("hi");
}
function deactivate() { }
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map