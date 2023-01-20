#!/usr/bin/env ts-node

console.log('Hello from TypeScript!');

var shell = require('shelljs');
var path = require('path');
shell.echo ("script runs");
var current_path_to_shell = path.join(__dirname, '..', 'src', 'server', 'virtualEnvPython.sh');

shell.exec('sh ' + current_path_to_shell)