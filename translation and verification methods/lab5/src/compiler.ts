import { c as C, Op, I32 } from "../../wasm";
import { Expr } from "../../lab04";
import { buildOneFunctionModule, Fn } from "./emitHelper";
const { i32, get_local} = C;
    
export function getVariables(e: Expr): string[] {
    const variables: string[] = [];
    const seen = new Set<string>();
    
    function collect(expr: Expr): void {
        switch (expr.type) {
            case 'num':
                break;
            case 'var':
                if (!seen.has(expr.name)) {
                    seen.add(expr.name);
                    variables.push(expr.name);
                }
                break;
            case 'binary':
                collect(expr.left);
                collect(expr.right);
                break;
            case 'neg':
                collect(expr.argument);
                break;
        }
    }
    
    collect(e);
    return variables;
}

export async function buildFunction(e: Expr, variables: string[]): Promise<Fn<number>>
{
    let expr = wasm(e, variables)
    return await buildOneFunctionModule("test", variables.length, [expr]);
}

function wasm(e: Expr, args: string[]): Op<I32> {
    function compile(expr: Expr): Op<I32> {
        switch (expr.type) {
            case 'num':
                return i32.const(expr.value);
            
            case 'var':
                const index = args.indexOf(expr.name);
                if (index === -1) {
                    throw new Error(`Variable ${expr.name} not found in function parameters`);
                }
                return get_local(i32, index);
            
            case 'binary':
                const left = compile(expr.left);
                const right = compile(expr.right);
                switch (expr.op) {
                    case '+':
                        return i32.add(left, right);
                    case '-':
                        return i32.sub(left, right);
                    case '*':
                        return i32.mul(left, right);
                    case '/':
                        return i32.div_s(left, right);
                }
                break;
            
            case 'neg':
                const arg = compile(expr.argument);
                return i32.sub(i32.const(0), arg);
        }
    }
    
    return compile(e);
}
