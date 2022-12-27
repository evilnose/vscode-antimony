import { QuickPickItem, window, Disposable, QuickInputButton, QuickInput, ExtensionContext, QuickInputButtons, commands, QuickPick, InputBox } from 'vscode';
import { sleep } from './utils/utils';
import { ProgressLocation } from 'vscode'
import * as vscode from 'vscode'

export async function modelSearchInput(context: ExtensionContext, initialEntity: string = null, selectedType: string = null) {
    let models = [];
    var modelList;

    interface State {
        title: string;
        step: number;
        totalSteps: number;
        model: QuickPickItem;
        entity: QuickPickItem;
        enteredModel: string;
    }

    async function collectInputs() {
        const state = {initialEntity} as Partial<State>;
        await MultiStepInput.run(input => inputQuery(input, state));
        return state as State;
    }

    const title = 'Browse Biomodels';

    async function inputQuery(input: MultiStepInput, state: Partial<State>) {
        const pick = await input.showInputBox({
            title,
            step: 1,
            totalSteps: 2,
            prompt: 'Enter query for model',
            value: "",
            shouldResume: shouldResume,
            validate: validateModelIsNotEmpty
        });
        // state.model = await input.showQuickPick({
        //     title,
        //     step: 1,
        //     totalSteps: 2,
        //     placeholder: 'Enter query for model',
        //     items: [],
        //     activeItem: null,
        //     shouldResume: shouldResume,
        //     onInputChanged: (value) => onQueryUpdated(value, input),
        // });
        state.enteredModel = pick
        await onQueryUpdated(pick, input);
        return (input: MultiStepInput) => pickBiomodel(input, state);
    }

    async function pickBiomodel(input: MultiStepInput, state: Partial<State>) {
        console.log(models)
        const pick = await input.showQuickPick({
            title,
            step: 2,
            totalSteps: 2,
            placeholder: 'Pick a biomodel',
            items: models,
            activeItem: state.model,
            shouldResume: shouldResume,
            onInputChanged: null,
        });
        state.entity = pick;
    }

    async function onQueryUpdated(query: string, input: MultiStepInput) {
        window.withProgress({
			location: ProgressLocation.Notification,
			title: "Searching for biomodels...",
			cancellable: true
		}, (progress, token) => {
            return commands.executeCommand('antimony.searchModel', query).then(async (result) => {
                modelList = result;
                for (let i = 0; i < modelList.length; i++) {
                    models.push({modelURL: modelList[i], index: i});
                }
                console.log("this is the model name: " + query)
                await input.onQueryResults(result);
            });
        })
    }

    async function validateModelIsNotEmpty(name: string) {
		await new Promise(resolve => setTimeout(resolve, 500));
		return name === '' ? 'Query is empty' : undefined;
	}

    function shouldResume() {
        // Could show a notification with the option to resume.
        return new Promise<boolean>((resolve, reject) => {
            // noop
        });
    }

    const state = await collectInputs();

}


// -------------------------------------------------------
// Helper code that wraps the API for the multi-step case.
// -------------------------------------------------------


class InputFlowAction {
    static back = new InputFlowAction();
    static cancel = new InputFlowAction();
    static resume = new InputFlowAction();
}

type InputStep = (input: MultiStepInput) => Thenable<InputStep | void>;

interface QuickPickParameters<T extends QuickPickItem> {
    title: string;
    step: number;
    totalSteps: number;
    items: T[];
    activeItem?: T;
    placeholder: string;
    buttons?: QuickInputButton[];
    initialValue?: string;
    shouldResume: () => Thenable<boolean>;
    onInputChanged: (v: string) => void;
}

interface InputBoxParameters {
    title: string;
    step: number;
    totalSteps: number;
    value: string;
    prompt: string;
    validate: (value: string) => Promise<string | undefined>;
    buttons?: QuickInputButton[];
    shouldResume: () => Thenable<boolean>;
}

export class MultiStepInput {

    static async run<T>(start: InputStep) {
        const input = new MultiStepInput();
        return input.stepThrough(start);
    }

    current?: QuickInput;
    private steps: InputStep[] = [];
    private lastErrorMillis = 0;

    private async stepThrough<T>(start: InputStep) {
        let step: InputStep | void = start;
        while (step) {
            this.steps.push(step);
            if (this.current) {
                this.current.enabled = false;
                this.current.busy = true;
            }
            try {
                step = await step(this);
            } catch (err) {
                if (err === InputFlowAction.back) {
                    this.steps.pop();
                    step = this.steps.pop();
                } else if (err === InputFlowAction.resume) {
                    step = this.steps.pop();
                } else if (err === InputFlowAction.cancel) {
                    step = undefined;
                } else {
                    throw err;
                }
            }
        }
        if (this.current) {
            this.current.dispose();
        }
    }

    async showQuickPick<T extends QuickPickItem, P extends QuickPickParameters<T>>(
        { title, step, totalSteps, items, activeItem, placeholder, buttons, initialValue, shouldResume, onInputChanged }: P) {
        const disposables: Disposable[] = [];
        try {
            return await new Promise<T | (P extends { buttons: (infer I)[] } ? I : never)>((resolve, reject) => {
                const input = window.createQuickPick<T>();
                input.title = title;
                input.step = step;
                input.totalSteps = totalSteps;
                input.placeholder = placeholder;
                input.items = items;
                if (initialValue) {
                    input.value = initialValue;
                    onInputChanged(initialValue);
                }
                if (activeItem) {
                    input.activeItems = [activeItem];
                }
                input.buttons = [
                    ...(this.steps.length > 1 ? [QuickInputButtons.Back] : []),
                    ...(buttons || [])
                ];
                disposables.push(
                    input.onDidTriggerButton(item => {
                        if (item === QuickInputButtons.Back) {
                            reject(InputFlowAction.back);
                        } else {
                            resolve(<any>item);
                        }
                    }),
                    input.onDidChangeSelection(items => resolve(items[0])),
                    input.onDidHide(() => {
                        (async () => {
                            reject(shouldResume && await shouldResume() ? InputFlowAction.resume : InputFlowAction.cancel);
                        })()
                            .catch(reject);
                    }),
                    ...(onInputChanged ? [input.onDidChangeValue(onInputChanged)] : []),
                );
                if (this.current) {
                    this.current.dispose();
                }
                this.current = input;
                this.current.show();
            });
        } finally {
            disposables.forEach(d => d.dispose());
        }
    }

    instanceOfQuickPick(input): input is QuickPick<QuickPickItem> {
        return 'items' in input;
    }

    async onQueryResults(result) {
        if (this.current && this.current.step === 2) {
            if (this.instanceOfQuickPick(this.current)) {
                if (result.error) {
                    this.current.items = [];

                    // Don't display errors too often
                    const curMillis = new Date().getTime();
                    if (curMillis - this.lastErrorMillis < 1000) {
                        return;
                    }
                    this.lastErrorMillis = curMillis;
                    window.showErrorMessage(`Could not perform query: ${result.error}`).then(() => console.log('finished'));
                    return;
                }

                if (this.current.value === result.query) {
                    if (result.items.length == 0) {
                        window.showInformationMessage("Biomodel not found")
                    }
                    this.current.items = result.items.map((item) => {
                        item['label'] = item['name'];
                        item['detail'] = item['detail'];
                        item['description'] = 'description';
                        item['alwaysShow'] = true;
                        return item;
                    });
                }
            }
        }
    }

    async showInputBox<P extends InputBoxParameters>({ title, step, totalSteps, value, prompt, validate, buttons, shouldResume }: P) {
        const disposables: Disposable[] = [];
        try {
            return await new Promise<string | (P extends { buttons: (infer I)[] } ? I : never)>((resolve, reject) => {
                const input = window.createInputBox();
                input.title = title;
                input.step = step;
                input.totalSteps = totalSteps;
                input.value = value || '';
                input.prompt = prompt;
                input.buttons = [
                    ...(this.steps.length > 1 ? [QuickInputButtons.Back] : []),
                    ...(buttons || [])
                ];
                let validating = validate('');
                disposables.push(
                    input.onDidTriggerButton(item => {
                        if (item === QuickInputButtons.Back) {
                            reject(InputFlowAction.back);
                        } else {
                            resolve(<any>item);
                        }
                    }),
                    input.onDidAccept(async () => {
                        const value = input.value;
                        input.enabled = false;
                        input.busy = true;
                        if (!(await validate(value))) {
                            resolve(value);
                        }
                        input.enabled = true;
                        input.busy = false;
                    }),
                    input.onDidChangeValue(async text => {
                        const current = validate(text);
                        validating = current;
                        const validationMessage = await current;
                        if (current === validating) {
                            input.validationMessage = validationMessage;
                        }
                    }),
                    input.onDidHide(() => {
                        (async () => {
                            reject(shouldResume && await shouldResume() ? InputFlowAction.resume : InputFlowAction.cancel);
                        })()
                            .catch(reject);
                    })
                );
                if (this.current) {
                    this.current.dispose();
                }
                this.current = input;
                this.current.show();
            });
        } finally {
            disposables.forEach(d => d.dispose());
        }
    }
}
