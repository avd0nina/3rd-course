import { Module, FunctionDef as BaseFunctionDef, While as BaseWhile, ParameterDef, FunctionCall } from 'lab08/src';
import * as arith from '../../lab04';

export interface AnnotatedModule extends Module {
    functions: FunctionDef[];
}

export interface FunctionDef extends BaseFunctionDef {
    requires?: Predicate;
    ensures?: Predicate;
}

export interface While extends BaseWhile {
    invariant?: Predicate;
}

export interface FunctionCallStatement {
    type: 'callStmt';
    call: FunctionCall;
}

export type Predicate = BoolLiteral | Comparison | NotPredicate | BinaryPredicate | Quantifier | FormulaRef;

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

export interface NotPredicate {
    type: 'not';
    argument: Predicate;
}

export interface BinaryPredicate {
    type: 'binPred';
    op: 'and' | 'or' | '->';
    left: Predicate;
    right: Predicate;
}

export interface Quantifier {
    type: 'quantifier';
    quantifier: 'forall' | 'exists';
    variable: ParameterDef;
    body: Predicate;
}

export interface FormulaRef {
    type: 'formulaRef';
    name: string;
    args: arith.Expr[];
}
