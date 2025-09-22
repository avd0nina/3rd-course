import { MatchResult } from "ohm-js";
import { rpnSemantics } from "./semantics";
import grammar from "./rpn.ohm-bundle";

export function evaluate(source: string): number {
    return calculate(parse(source));
}

export function maxStackDepth(source: string): number {
    return calculateStackDepth(parse(source));
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

function calculate(expression: MatchResult): number {
    return rpnSemantics(expression).calculate();
}

function calculateStackDepth(expression: MatchResult): number {
    return rpnSemantics(expression).stackDepth.max;
}
