import { EnclaveContext } from "kurtosis-sdk";
import { Result, ok, err } from "neverthrow";
import * as log from "loglevel";
import { ExecutableKurtosisModule } from "kurtosis-module-api-lib";

const TIPS_REPOSITORY: string[] = [
    "Everything not saved will be lost.",
    "Don't pet a burning dog.",
    "Even a broken clock is right twice a day.",
    "If no one comes from the future to stop you from doing it, then how bad of a decision can it really be?",
    "Never fall in love with a tennis player. Love means nothing to them.",
    "If you ever get caught sleeping on the job, slowly raise your head and say 'In Jesus' name, Amen'",
    "Never trust in an electrician with no eyebrows",
    "If you sleep until lunch time, you can save the breakfast money.",
];

// Parameters that the execute command accepts, serialized as JSON
interface ExecuteParams {
    iWantATip: boolean;
}

// Result that the execute command returns, serialized as JSON
class ExecuteResult {
    readonly tip: string

    constructor(tip: string) {
        this.tip = tip;
    }
}

export class ExampleExecutableKurtosisModule implements ExecutableKurtosisModule {
    constructor() {}

    async execute(networkCtx: EnclaveContext, serializedParams: string): Promise<Result<string, Error>> {
        log.info(`Received serialized execute params:\n${serializedParams}`);
        let params: ExecuteParams;
        try {
            params = JSON.parse(serializedParams)
        } catch (e: any) {
            // Sadly, we have to do this because there's no great way to enforce the caught thing being an error
            // See: https://stackoverflow.com/questions/30469261/checking-for-typeof-error-in-js
            if (e && e.stack && e.message) {
                return err(e as Error);
            }
            return err(new Error("Parsing params string '" + serializedParams + "' threw an exception, but " +
                "it's not an Error so we can't report any more information than this"));
        }

        const resultObj: ExecuteResult = new ExecuteResult(
            ExampleExecutableKurtosisModule.getRandomTip(params.iWantATip)
        );

        let stringResult;
        try {
            stringResult = JSON.stringify(resultObj);
        } catch (e: any) {
            // Sadly, we have to do this because there's no great way to enforce the caught thing being an error
            // See: https://stackoverflow.com/questions/30469261/checking-for-typeof-error-in-js
            if (e && e.stack && e.message) {
                return err(e as Error);
            }
            return err(new Error("Serializing the Kurtosis module result threw an exception, but " +
                "it's not an Error so we can't report any more information than this"));
        }

        log.info("Execution successful")
        return ok(stringResult);
    }

    private static getRandomTip(shouldGiveAdvice: boolean): string {
        let tip: string;
        if (shouldGiveAdvice) {
            // This gives a random number between [0, length)
            tip = TIPS_REPOSITORY[Math.floor(Math.random() * TIPS_REPOSITORY.length)];
        } else {
            tip = "The module won't enlighten you today."
        }
        return tip
    }
}