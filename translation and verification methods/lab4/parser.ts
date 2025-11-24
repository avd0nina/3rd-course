import { MatchResult, Node } from 'ohm-js';
import { arithGrammar, ArithmeticActionDict, ArithmeticSemantics, SyntaxError } from '../../lab03';
import { Expr, BinaryOp, UnaryNeg, NumLiteral, Variable } from './ast';

export const getExprAst: ArithmeticActionDict<Expr> = {
    Expr(addExpr: Node) {
        return addExpr.parse();
    },
    
    AddExpr(first: Node, ops: Node, operands: Node) {
        let result = first.parse();
        for (let i = 0; i < ops.numChildren; i++) {
            const op = ops.child(i).sourceString as '+' | '-';
            const right = operands.child(i).parse();
            result = { type: 'binary', op, left: result, right } as BinaryOp;
        }
        return result;
    },
    
    MulExpr(first: Node, ops: Node, operands: Node) {
        let result = first.parse();
        for (let i = 0; i < ops.numChildren; i++) {
            const op = ops.child(i).sourceString as '*' | '/';
            const right = operands.child(i).parse();
            result = { type: 'binary', op, left: result, right } as BinaryOp;
        }
        return result;
    },
    
    UnaryExpr_neg(_minus: Node, expr: Node) {
        return { type: 'neg', argument: expr.parse() } as UnaryNeg;
    },
    
    UnaryExpr_pos(primary: Node) {
        return primary.parse();
    },
    
    PrimaryExpr_paren(_open: Node, expr: Node, _close: Node) {
        return expr.parse();
    },
    
    PrimaryExpr_num(num: Node) {
        return { type: 'num', value: parseInt(num.sourceString) } as NumLiteral;
    },
    
    PrimaryExpr_var(v: Node) {
        return { type: 'var', name: v.sourceString } as Variable;
    },
}

export const semantics = arithGrammar.createSemantics();
semantics.addOperation("parse()", getExprAst);

export interface ArithSemanticsExt extends ArithmeticSemantics {
    (match: MatchResult): ArithActionsExt
}

export interface ArithActionsExt {
    parse(): Expr
}
export function parseExpr(source: string): Expr {
    const match = arithGrammar.match(source);
    if (match.failed()) {
        throw new SyntaxError(match.message);
    }
    return (semantics(match) as ArithActionsExt).parse();
}
