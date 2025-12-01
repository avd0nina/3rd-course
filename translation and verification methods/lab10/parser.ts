import { MatchResult, Semantics } from 'ohm-js';
import { getExprAst } from '../../lab04';
import { getFunnyAst as lab08Actions } from '../../lab08/src/parser';
import * as ast from './funnier';
import * as arith from '../../lab04';

import grammar, { FunnierActionDict } from './funnier.ohm-bundle';

import { AnnotatedModule } from './funnier';

const getFunnierAst = {
    ...lab08Actions,
    ...getExprAst,
    
    Module(functions: any) {
        return {
            type: 'module',
            functions: functions.children.map((f: any) => f.parse())
        } as ast.AnnotatedModule;
    },

    FunctionDef(name: any, _lp: any, params: any, _rp: any, _req: any, req: any, _ret: any, returns: any, _ens: any, ens: any, _uses: any, locals: any, body: any) {
        return {
            type: 'fun',
            name: name.sourceString,
            parameters: params.children.length > 0 ? params.child(0).parse() : [],
            returns: returns.parse(),
            locals: locals.children.length > 0 ? locals.child(0).parse() : [],
            requires: req.children.length > 0 ? req.child(0).parse() : undefined,
            ensures: ens.children.length > 0 ? ens.child(0).parse() : undefined,
            body: body.parse()
        } as ast.FunctionDef;
    },

    ReturnSpec_void(_void: any) {
        return [];
    },

    ReturnSpec_params(params: any) {
        return params.parse();
    },

    While(_while: any, _lp: any, cond: any, _rp: any, _invKw: any, _invLp: any, inv: any, _invRp: any, body: any) {
        return {
            type: 'while',
            condition: cond.parse(),
            invariant: inv.children.length > 0 ? inv.child(0).parse() : undefined,
            body: body.parse()
        } as ast.While;
    },

    OrPredicate_or(left: any, _or: any, right: any) {
        return {
            type: 'binPred',
            op: 'or',
            left: left.parse(),
            right: right.parse()
        } as ast.BinaryPredicate;
    },

    AndPredicate_and(left: any, _and: any, right: any) {
        return {
            type: 'binPred',
            op: 'and',
            left: left.parse(),
            right: right.parse()
        } as ast.BinaryPredicate;
    },

    ImpliesPredicate_implies(left: any, _arrow: any, right: any) {
        return {
            type: 'binPred',
            op: '->',
            left: left.parse(),
            right: right.parse()
        } as ast.BinaryPredicate;
    },

    NotPredicate_not(_not: any, pred: any) {
        return {
            type: 'not',
            argument: pred.parse()
        } as ast.NotPredicate;
    },

    PrimaryPredicate_true(_true: any) {
        return {
            type: 'bool',
            value: true
        } as ast.BoolLiteral;
    },

    PrimaryPredicate_false(_false: any) {
        return {
            type: 'bool',
            value: false
        } as ast.BoolLiteral;
    },

    PrimaryPredicate_comp(comp: any) {
        return comp.parse();
    },

    PrimaryPredicate_quant(quant: any) {
        return quant.parse();
    },

    PrimaryPredicate_formula(formula: any) {
        return formula.parse();
    },

    PrimaryPredicate_paren(_lp: any, pred: any, _rp: any) {
        return pred.parse();
    },

    Quantifier(quantType: any, _lp: any, varDef: any, _pipe: any, body: any, _rp: any) {
        return {
            type: 'quantifier',
            quantifier: quantType.sourceString as 'forall' | 'exists',
            variable: varDef.parse(),
            body: body.parse()
        } as ast.Quantifier;
    },

    FormulaRef(name: any, _lp: any, args: any, _rp: any) {
        return {
            type: 'formulaRef',
            name: name.sourceString,
            args: args.asIteration().children.map((a: any) => a.parse())
        } as ast.FormulaRef;
    },

    FunctionCallStatement(call: any, _semi: any) {
        return {
            type: 'callStmt',
            call: call.parse()
        } as ast.FunctionCallStatement;
    }
};

export const semantics: FunnySemanticsExt = grammar.Funnier.createSemantics() as FunnySemanticsExt;
semantics.addOperation("parse()", getFunnierAst);
export interface FunnySemanticsExt extends Semantics {
    (match: MatchResult): FunnyActionsExt
}

interface FunnyActionsExt {
    parse(): AnnotatedModule;
}

export function parseFunnier(source: string, origin?: string): AnnotatedModule {
    const match = grammar.Funnier.match(source, 'Module');
    if (match.failed()) {
        throw new Error(match.message || "Syntax error");
    }
    const module = (semantics(match) as FunnyActionsExt).parse();
    return module;
}
