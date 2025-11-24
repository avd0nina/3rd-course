import { MatchResult } from "ohm-js";
import grammar, { ArithmeticActionDict, ArithmeticSemantics } from "./arith.ohm-bundle";

export const arithSemantics: ArithSemantics = grammar.createSemantics() as ArithSemantics;


const arithCalc = {
    Expr(addExpr) {
        return addExpr.calculate(this.args.params);
    },
    
    AddExpr(first, _ops, operands) {
        let result = first.calculate(this.args.params);
        const ops = _ops.children;
        const vals = operands.children;
        for (let i = 0; i < ops.length; i++) {
            const op = ops[i].sourceString;
            const operand = vals[i].calculate(this.args.params);
            if (op === '+') {
                result = result + operand;
            } else {
                result = result - operand;
            }
        }
        return result;
    },
    
    MulExpr(first, _ops, operands) {
        let result = first.calculate(this.args.params);
        const ops = _ops.children;
        const vals = operands.children;
        for (let i = 0; i < ops.length; i++) {
            const op = ops[i].sourceString;
            const operand = vals[i].calculate(this.args.params);
            if (op === '*') {
                result = result * operand;
            } else {
                if (operand === 0) {
                    throw new Error("Division by zero");
                }
                result = result / operand;
            }
        }
        return result;
    },
    
    UnaryExpr_neg(_minus, expr) {
        return -expr.calculate(this.args.params);
    },
    
    UnaryExpr_pos(expr) {
        return expr.calculate(this.args.params);
    },
    
    PrimaryExpr_paren(_open, expr, _close) {
        return expr.calculate(this.args.params);
    },
    
    PrimaryExpr_num(number) {
        return parseInt(number.sourceString, 10);
    },
    
    PrimaryExpr_var(variable) {
        const varName = variable.sourceString;
        const value = this.args.params[varName];
        return value !== undefined ? value : NaN;
    }
} satisfies ArithmeticActionDict<number | undefined>;


arithSemantics.addOperation<Number>("calculate(params)", arithCalc);


export interface ArithActions {
    calculate(params: {[name:string]:number}): number;
}

export interface ArithSemantics extends ArithmeticSemantics {
    (match: MatchResult): ArithActions;
}
