import { ReversePolishNotationActionDict } from "./rpn.ohm-bundle";

export const rpnStackDepth = {
    Rpn(expr) {
        return expr.stackDepth;
    },
    Expr_number(num) {
        return num.stackDepth;
    },
    Expr_add(left, right, _plus) {
        const leftDepth = left.stackDepth;
        const rightDepth = right.stackDepth;
        return {
            max: Math.max(leftDepth.max, leftDepth.out + rightDepth.max),
            out: leftDepth.out + rightDepth.out - 1
        };
    },
    Expr_multiply(left, right, _times) {
        const leftDepth = left.stackDepth;
        const rightDepth = right.stackDepth;
        return {
            max: Math.max(leftDepth.max, leftDepth.out + rightDepth.max),
            out: leftDepth.out + rightDepth.out - 1
        };
    },
    number(_space1, _digits, _space2) {
        return { max: 1, out: 1 };
    }
} satisfies ReversePolishNotationActionDict<StackDepth>;
export type StackDepth = {max: number, out: number};
