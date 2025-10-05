import { MatchResult, Node } from 'ohm-js';
import { arithGrammar, ArithmeticActionDict, ArithmeticSemantics, SyntaxError } from '../../lab03';
import { Expr } from './ast';

export const getExprAst: ArithmeticActionDict<Expr> = {
    Expr(e: Node): Expr {
        return e.parse();
    },

    Sum(first: Node, operators: Node, rest: Node): Expr {
        let acc: Expr = first.parse();
        const n = operators.children.length;
        for (let i = 0; i < n; i++) {
            const op = operators.child(i).sourceString as '+' | '-';
            const rhs: Expr = rest.child(i).parse();
            acc = { type: 'bin', op, left: acc, right: rhs };
        }
        return acc;
    },

    Mul(first: Node, operators: Node, rest: Node): Expr {
        let acc: Expr = first.parse();
        const n = operators.children.length;
        for (let i = 0; i < n; i++) {
            const op = operators.child(i).sourceString as '*' | '/';
            const rhs: Expr = rest.child(i).parse();
            acc = { type: 'bin', op, left: acc, right: rhs };
        }
        return acc;
    },

    Unary_neg(_minus: Node, u: Node): Expr {
        return { type: 'neg', arg: u.parse() };
    },

    Primary_num(n: Node): Expr {
        return { type: 'num', value: parseInt(n.sourceString, 10) };
    },

    Primary_var(v: Node): Expr {
        return { type: 'var', name: v.sourceString };
    },

    Primary_parens(_open: Node, e: Node, _close: Node): Expr {
        return e.parse();
    },
};

export const semantics = arithGrammar.createSemantics();

semantics.addOperation<Expr>('parse()', getExprAst);

export interface ArithSemanticsExt extends ArithmeticSemantics {
    (match: MatchResult): ArithActionsExt;
}

export interface ArithActionsExt {
    parse(): Expr;
}

export function parseExpr(source: string): Expr {
    const match = arithGrammar.match(source, 'Expr');
    if (match.failed()) {
        const msg = (match as any).message ?? 'Syntax error while parsing expression.';
        throw new SyntaxError(msg);
    }
    return (semantics as ArithSemanticsExt)(match).parse();
}
