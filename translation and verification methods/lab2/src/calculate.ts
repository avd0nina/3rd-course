import { ReversePolishNotationActionDict} from "./rpn.ohm-bundle";

export const rpnCalc = {
    Rpn(expr) {
        return expr.calculate();
    },
    Expr_number(num) {
        return num.calculate();
    },
    Expr_add(left, right, _plus) {
        return left.calculate() + right.calculate();
    },
    Expr_multiply(left, right, _times) {
        return left.calculate() * right.calculate();
    },
    number(_space1, _digits, _space2) {
        return parseInt(this.sourceString);
    }
} satisfies ReversePolishNotationActionDict<number>;
