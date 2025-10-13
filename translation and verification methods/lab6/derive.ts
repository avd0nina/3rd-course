import { Expr } from "../../lab04";

type Op = '+' | '-' | '*' | '/';

const num = (n: number): Expr => ({ type: 'num', value: n });
const neg = (e: Expr): Expr => ({ type: 'neg', arg: e });
const bin = (op: Op, l: Expr, r: Expr): Expr => ({ type: 'bin', op, left: l, right: r });

export function derive(e: Expr, varName: string): Expr {
    return simplify(d(e, varName));
}

function d(e: Expr, x: string): Expr {
    switch (e.type) {
        case 'num':
            return num(0);
        case 'var':
            return num(e.name === x ? 1 : 0);
        case 'neg':
            return neg(d(e.arg, x));
        case 'bin': {
            const f = e.left;
            const g = e.right;
            const f1 = d(f, x);
            const g1 = d(g, x);
            switch (e.op) {
                case '+': return bin('+', f1, g1);
                case '-': return bin('-', f1, g1);
                case '*':
                    return bin('+', bin('*', f1, g), bin('*', f, g1));
                case '/':
                    return bin(
                        '/',
                        bin('-', bin('*', f1, g), bin('*', f, g1)),
                        bin('*', g, g)
                    );
            }
        }
    }
}

function simplify(e: Expr): Expr {
    switch (e.type) {
        case 'num':
        case 'var':
            return e;
        case 'neg': {
            const a = simplify(e.arg);
            if (a.type === 'neg') return simplify(a.arg);
            if (a.type === 'num') return num(a.value === 0 ? 0 : -a.value);
            if (a.type === 'bin' && a.op === '/') {
                if (a.left.type === 'neg') return bin('/', a.left.arg, a.right);
                if (a.left.type === 'num') return bin('/', num(-a.left.value), a.right);
            }
            return { type: 'neg', arg: a };
        }
        case 'bin': {
            const l = simplify(e.left);
            const r = simplify(e.right);
            if (l.type === 'num' && r.type === 'num') {
                switch (e.op) {
                    case '+': return num(l.value + r.value);
                    case '-': return num(l.value - r.value);
                    case '*': return num(l.value * r.value);
                    case '/': return num((l.value / r.value) | 0);
                }
            }
            switch (e.op) {
                case '+': {
                    if (isZero(l)) return r;
                    if (isZero(r)) return l;
                    return bin('+', l, r);
                }
                case '-': {
                    if (isZero(r)) return l;
                    if (isZero(l)) return simplify(neg(r));
                    return bin('-', l, r);
                }
                case '*': {
                    if (isZero(l) || isZero(r)) return num(0);
                    if (isOne(l)) return r;
                    if (isOne(r)) return l;
                    return bin('*', l, r);
                }
                case '/': {
                    if (isOne(r)) return l;
                    return bin('/', l, r);
                }
            }
        }
    }
}

function isZero(e: Expr): boolean {
    return e.type === 'num' && e.value === 0;
}

function isOne(e: Expr): boolean {
    return e.type === 'num' && e.value === 1;
}
