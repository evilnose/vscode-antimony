import * as cp from "child_process";

export function sleep(ms) {
	return new Promise(resolve => setTimeout(resolve, ms));
}

// convert cp.exec to a promise
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
