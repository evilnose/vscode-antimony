/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/
import * as path from 'path';

import { runTests } from 'vscode-test';

async function main() {
	try {
        // Development root folder
		const extensionDevelopmentPath = path.resolve(__dirname, '../../../');

        // Main test file
		const extensionTestsPath = path.resolve(__dirname, './index');

        // Run integration tests
		await runTests({
			extensionDevelopmentPath,
			extensionTestsPath,
			launchArgs: ['--disable-extensions'],
		});
	} catch (err) {
		console.error('Failed to run tests');
		process.exit(1);
	}
}

main();
