import { Expr, parseExpr } from "../../lab04";
import { buildFunction, getVariables } from "./compiler";
import { Fn } from "./emitHelper";

export async function parseCompileAndExecute(expression: string, ...args: number[]): Promise<number> {
    let expr = parseExpr(expression);
    let variables = getVariables(expr);
    return await compileAndExecute(expr, variables, ...args);
}
export async function compileAndExecute(expr: Expr, variables: string[], ...args: number[]): Promise<number>
{
    let wasmFunc = await compile(expr, variables);
    return wasmFunc(...args);
}

export const compile = async (expr: Expr, variables: string[]) => checked(await buildFunction(expr, variables));

export const checked = <R>(func: Fn<R>): Fn<R> => function(...args: number[]): R
    {
        if(args.length != func.length)
            throw new WebAssembly.RuntimeError(`Signature mismatch: passed ${args.length}, expected ${func.length}.`);
        return func(...args);
    };

export { buildFunction, getVariables } from "./compiler";
