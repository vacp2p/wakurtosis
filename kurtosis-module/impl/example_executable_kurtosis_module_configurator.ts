import { Result, err, ok } from 'neverthrow';
import * as log from 'loglevel';
import { ExampleExecutableKurtosisModule } from './example_executable_kurtosis_module';
import { ExecutableKurtosisModule, KurtosisModuleConfigurator } from 'kurtosis-module-api-lib';

const DEFAULT_LOG_LEVEL: string = "info";

// Parameters that the module accepts when loaded, serializeda as JSON
interface LoadModuleParams {
    logLevel: string;
}

type LoglevelAcceptableLevelStrs = log.LogLevelDesc

export class ExampleExecutableKurtosisModuleConfigurator implements KurtosisModuleConfigurator {
    public parseParamsAndCreateExecutableModule(serializedCustomParamsStr: string): Result<ExecutableKurtosisModule, Error> {
        let args: LoadModuleParams;
        try {
            args = JSON.parse(serializedCustomParamsStr);
        } catch (e: any) {
            // Sadly, we have to do this because there's no great way to enforce the caught thing being an error
            // See: https://stackoverflow.com/questions/30469261/checking-for-typeof-error-in-js
            if (e && e.stack && e.message) {
                return err(e as Error);
            }
            return err(new Error("Parsing params string '" + serializedCustomParamsStr + "' threw an exception, but " +
                "it's not an Error so we can't report any more information than this"));
        }

        const setLogLevelResult: Result<null, Error> = ExampleExecutableKurtosisModuleConfigurator.setLogLevel(args.logLevel)
        if (setLogLevelResult.isErr()) {
            console.log("Error in setting the log level")
            return err(setLogLevelResult.error);
        }

        const module: ExampleExecutableKurtosisModule = new ExampleExecutableKurtosisModule();
        return ok(module);
    }

    private static setLogLevel(logLevelStr: string): Result<null, Error> {
        let logLevelDescStr: string = logLevelStr;
        if (logLevelStr === null || logLevelStr === undefined || logLevelStr === "") {
            logLevelDescStr = DEFAULT_LOG_LEVEL;
        }
        const logLevelDesc: log.LogLevelDesc = logLevelDescStr as log.LogLevelDesc
        log.setLevel(logLevelDesc);
        return ok(null);
    }
}
