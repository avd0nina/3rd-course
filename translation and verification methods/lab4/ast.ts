export interface NumLiteral {
    type: 'num';
    value: number;
}

export interface Variable {
    type: 'var';
    name: string;
}

export interface BinaryOp {
    type: 'binary';
    op: '+' | '-' | '*' | '/';
    left: Expr;
    right: Expr;
}

export interface UnaryNeg {
    type: 'neg';
    argument: Expr;
}

export type Expr = NumLiteral | Variable | BinaryOp | UnaryNeg;
