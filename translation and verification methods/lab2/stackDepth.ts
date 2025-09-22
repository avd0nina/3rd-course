import { ReversePolishNotationActionDict } from "./rpn.ohm-bundle";

export const rpnStackDepth = {
    Expr_num(_n) {
        const out = 1;
        const max = 1;
        return { max, out };
    },

    Expr_summ(first, second, _summ) {
        const F = first.stackDepth;
        const S = second.stackDepth;
        const out = F.out + S.out - 1;
        const max = Math.max(F.max, F.out + S.max);
        return { max, out };
    },

    Expr_mult(first, second, _mult) {
        const F = first.stackDepth;
        const S = second.stackDepth;
        const out = F.out + S.out - 1;
        const max = Math.max(F.max, F.out + S.max);
        return { max, out };
    },
} satisfies ReversePolishNotationActionDict<StackDepth>;

export type StackDepth = { max: number, out: number };
