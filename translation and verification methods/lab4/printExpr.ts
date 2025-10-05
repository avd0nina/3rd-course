import { Bin, Expr } from "./ast";

function prec(e: Expr): number {
    switch (e.type) {
        case 'num':
        case 'var': return 4;
        case 'neg': return 3;
        case 'bin':
            return (e.op === '+' || e.op === '-') ? 1 : 2;
    }
}

function isBinOp(e: Expr, ops: Array<Bin['op']>): e is Bin {
    return e.type === 'bin' && ops.includes(e.op);
}

function needParens(child: Expr, parentOp: Bin['op'], isRightChild: boolean): boolean {
    const pc = prec(child);
    const pp = (parentOp === '+' || parentOp === '-') ? 1 : 2;

    if (pc > pp) return false;
    if (pc < pp) return true;

    if (child.type !== 'bin') return false;

    if (parentOp === '+') {
        return false;
    }
    if (parentOp === '-') {
        return isRightChild && isBinOp(child, ['+', '-']);
    }

    if (parentOp === '*') {
        return isRightChild && isBinOp(child, ['/']);
    }
    if (parentOp === '/') {
        return isRightChild && isBinOp(child, ['*', '/']);
    }
    return false;
}

export function printExpr(e: Expr, parentOp?: Bin['op'], isRightChild: boolean = false): string {
    switch (e.type) {
        case 'num': return String(e.value);
        case 'var': return e.name;
        case 'neg': {
            const inner = (e.arg.type === 'bin')
                ? `(${printExpr(e.arg)})`
                : printExpr(e.arg);
            return `-${inner}`;
        }
        case 'bin': {
            const L = needParens(e.left, e.op, false)
                ? `(${printExpr(e.left)})`
                : printExpr(e.left);
            const R = needParens(e.right, e.op, true)
                ? `(${printExpr(e.right)})`
                : printExpr(e.right);

            const opStr = ` ${e.op} `;
            const s = `${L}${opStr}${R}`;

            if (parentOp && needParens(e, parentOp, isRightChild)) {
                return `(${s})`;
            }
            return s;
        }
    }
}
