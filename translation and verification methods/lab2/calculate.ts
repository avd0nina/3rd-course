import { ReversePolishNotationActionDict } from "./rpn.ohm-bundle";

export const rpnCalc = {
    Expr_num(n) {
        return parseInt(n.sourceString, 10);
    },

    Expr_summ(first, second, _summ) {
        return first.calculate() + second.calculate();
    },

    Expr_mult(first, second, _mult) {
        return first.calculate() * second.calculate();
    }
} satisfies ReversePolishNotationActionDict<number>;
