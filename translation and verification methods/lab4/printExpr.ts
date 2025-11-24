import { Expr } from "./ast";

type OpPrecedence = number;

const PRECEDENCE = {
    '+': 1,
    '-': 1,
    '*': 2,
    '/': 2,
} as const;

function getPrecedence(expr: Expr): OpPrecedence {
    if (expr.type === 'binary') {
        return PRECEDENCE[expr.op];
    }
    return Infinity;
}

function needsParens(expr: Expr, parentOp?: string, isRight?: boolean): boolean {
    if (expr.type !== 'binary') {
        return false;
    }
    if (!parentOp) {
        return false;
    }
    const exprPrec = getPrecedence(expr);
    const parentPrec = PRECEDENCE[parentOp as keyof typeof PRECEDENCE];
    if (exprPrec < parentPrec) {
        return true;
    }
    if (isRight && exprPrec === parentPrec && (parentOp === '-' || parentOp === '/')) {
        return true;
    }
    return false;
}

export function printExpr(e: Expr, parentOp?: string, isRight?: boolean): string
{
    switch (e.type) {
        case 'num':
            return e.value.toString();
        
        case 'var':
            return e.name;
        
        case 'neg':
            return '-' + printExpr(e.argument);
        
        case 'binary': {
            const left = printExpr(e.left, e.op, false);
            const right = printExpr(e.right, e.op, true);
            const result = left + ' ' + e.op + ' ' + right;
            if (needsParens(e, parentOp, isRight)) {
                return '(' + result + ')';
            }
            return result;
        }
    }
}
