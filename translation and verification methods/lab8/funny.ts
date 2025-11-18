import * as arith from "../../lab04";

export interface Module {
    type: 'module';
    functions: FunctionDef[]
}

export interface FunctionDef {
    type: 'fun';
    name: string;
    parameters: ParameterDef[];
    returns: ParameterDef[];
    locals: ParameterDef[];
    body: Statement;
}

export interface ParameterDef {
    type: "param";
    name: string;
    varType: VarType;
}

export type VarType = 'int' | 'int[]';

export type Statement = Assignment | Block | Conditional | While;
export interface Assignment {
    type: 'assign';
    kind: 'simple' | 'array' | 'tuple';
    targets: string[];
    indices?: arith.Expr[];
    value: arith.Expr | FunctionCall;
}
export interface Block {
    type: 'block';
    statements: Statement[];
}
export interface Conditional {
    type: 'if';
    condition: Condition;
    thenBranch: Statement;
    elseBranch?: Statement;
}
export interface While {
    type: 'while';
    condition: Condition;
    body: Statement;
}

export type Condition = BoolLiteral | Comparison | NotCondition | BinaryCondition;
export interface BoolLiteral {
    type: 'bool';
    value: boolean;
}
export interface Comparison {
    type: 'comp';
    op: '==' | '!=' | '<' | '<=' | '>' | '>=';
    left: arith.Expr;
    right: arith.Expr;
}
export interface NotCondition {
    type: 'not';
    argument: Condition;
}
export interface BinaryCondition {
    type: 'binCond';
    op: 'and' | 'or' | '->';
    left: Condition;
    right: Condition;
}

export interface FunctionCall {
    type: 'call';
    name: string;
    args: arith.Expr[];
}
export interface ArrayAccess {
    type: 'arrayAccess';
    name: string;
    index: arith.Expr;
}
