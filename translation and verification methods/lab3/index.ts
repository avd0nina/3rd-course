import { MatchResult } from "ohm-js";
import grammar from "./arith.ohm-bundle";
import { arithSemantics } from "./calculate";

export const arithGrammar = grammar;
export { ArithmeticActionDict, ArithmeticSemantics } from './arith.ohm-bundle';

export function evaluate(content: string, params?: { [name: string]: number }): number {
    return calculate(parse(content), params ?? {});
}

export class SyntaxError extends Error {
}

function parse(content: string): MatchResult {
    const match = grammar.match(content, "Expr");
    if (match.failed()) {
        const msg = (match as any).message ?? "Syntax error while parsing expression.";
        throw new SyntaxError(msg);
    }
    return match;
}

function calculate(expression: MatchResult, params: { [name: string]: number }): number {
    return arithSemantics(expression).calculate(params);
}
