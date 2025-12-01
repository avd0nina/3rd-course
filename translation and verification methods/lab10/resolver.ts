import * as ast from "./funnier";
import * as lab08 from "../../lab08/src";
import * as arith from "../../lab04";

export function resolveModule(m: ast.AnnotatedModule): ast.AnnotatedModule {
    for (const func of m.functions) {
        const scope = new Map<string, { varType: lab08.VarType }>();
        for (const param of func.parameters) {
            scope.set(param.name, { varType: param.varType });
        }
        for (const ret of func.returns) {
            scope.set(ret.name, { varType: ret.varType });
        }
        for (const local of func.locals) {
            scope.set(local.name, { varType: local.varType });
        }
        if (func.requires) {
            validatePredicate(func.requires, scope, m.functions);
        }
        if (func.ensures) {
            validatePredicate(func.ensures, scope, m.functions);
        }
        validateStatementPredicates(func.body, scope, m.functions);
    }
    return m;
}

function validatePredicate(
    pred: ast.Predicate,
    scope: Map<string, { varType: lab08.VarType }>,
    functions: ast.FunctionDef[]
): void {
    switch (pred.type) {
        case 'bool':
            break;
        case 'comp':
            validateExprInPredicate(pred.left, scope);
            validateExprInPredicate(pred.right, scope);
            break;
        case 'not':
            validatePredicate(pred.argument, scope, functions);
            break;
        case 'binPred':
            validatePredicate(pred.left, scope, functions);
            validatePredicate(pred.right, scope, functions);
            break;
        case 'quantifier':
            const extendedScope = new Map(scope);
            extendedScope.set(pred.variable.name, { varType: pred.variable.varType });
            validatePredicate(pred.body, extendedScope, functions);
            break;
        case 'formulaRef':
            for (const arg of pred.args) {
                validateExprInPredicate(arg, scope);
            }
            break;
    }
}

function validateExprInPredicate(
    expr: arith.Expr | lab08.ArrayAccess | lab08.FunctionCall,
    scope: Map<string, { varType: lab08.VarType }>
): void {
    if ('type' in expr) {
        switch (expr.type) {
            case 'var':
                if (!scope.has(expr.name)) {
                    throw new Error(`Undeclared variable '${expr.name}' in predicate`);
                }
                break;
            case 'arrayAccess':
                if (!scope.has(expr.name)) {
                    throw new Error(`Undeclared array '${expr.name}' in predicate`);
                }
                validateExprInPredicate(expr.index, scope);
                break;
            case 'call':
                for (const arg of expr.args) {
                    validateExprInPredicate(arg, scope);
                }
                break;
            case 'binary':
                validateExprInPredicate(expr.left, scope);
                validateExprInPredicate(expr.right, scope);
                break;
            case 'neg':
                validateExprInPredicate(expr.argument, scope);
                break;
        }
    }
}

function validateStatementPredicates(
    stmt: lab08.Statement | ast.FunctionCallStatement,
    scope: Map<string, { varType: lab08.VarType }>,
    functions: ast.FunctionDef[]
): void {
    if ('type' in stmt) {
        switch (stmt.type) {
            case 'block':
                for (const s of stmt.statements) {
                    validateStatementPredicates(s, scope, functions);
                }
                break;
            case 'if':
                validateStatementPredicates(stmt.thenBranch, scope, functions);
                if (stmt.elseBranch) {
                    validateStatementPredicates(stmt.elseBranch, scope, functions);
                }
                break;
            case 'while':
                const whileStmt = stmt as ast.While;
                if (whileStmt.invariant) {
                    validatePredicate(whileStmt.invariant, scope, functions);
                }
                validateStatementPredicates(whileStmt.body, scope, functions);
                break;
            case 'callStmt':
                break;
            case 'assign':
                break;
        }
    }
}
