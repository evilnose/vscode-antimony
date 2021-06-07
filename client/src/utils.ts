import * as cp from "child_process";

export function sleep(ms) {
	return new Promise(resolve => setTimeout(resolve, ms));
}

export function execPromise(command: string) {
    return new Promise(function (resolve, reject) {
        cp.exec(command, (err, stdout, stderr) => {
            if (err) {
                reject(err);
            } else {
                resolve({
                    stdout,
                    stderr,
                });
            }
        })
    });
}
