import { getExprAst } from '../../lab04';
import * as ast from './funny';
import * as arith from '../../lab04';
import { FunnyError } from './index';

import grammar, { FunnyActionDict } from './funny.ohm-bundle';

import { MatchResult, Semantics, Node } from 'ohm-js';

export const getFunnyAst = {
    Module(functions: any) {
        return {
            type: 'module',
            functions: functions.children.map((f: any) => f.parse())
        } as ast.Module;
    },

    FunctionDef(name: any, _lp: any, params: any, _rp: any, _req: any, req: any, _ret: any, returns: any, _ens: any, ens: any, _uses: any, locals: any, body: any) {
        return {
            type: 'fun',
            name: name.sourceString,
            parameters: params.children.length > 0 ? params.child(0).parse() : [],
            returns: returns.parse(),
            locals: locals.children.length > 0 ? locals.child(0).parse() : [],
            body: body.parse()
        } as ast.FunctionDef;
    },

    ParameterList(first: any, _commas: any, rest: any) {
        return [first.parse(), ...rest.children.map((n: any) => n.parse())];
    },

    LocalsList(first: any, _commas: any, rest: any) {
        return [first.parse(), ...rest.children.map((n: any) => n.parse())];
    },

    VariableDef(name: any, _colon: any, type: any) {
        return {
            type: 'param',
            name: name.sourceString,
            varType: type.parse()
        } as ast.ParameterDef;
    },

    LocalDef(name: any, _colon: any, _int: any) {
        return {
            type: 'param',
            name: name.sourceString,
            varType: 'int'
        } as ast.ParameterDef;
    },

    Type_array(_int: any, _lb: any) {
        return 'int[]' as ast.VarType;
    },

    Type_int(_int: any) {
        return 'int' as ast.VarType;
    },

    Block(_lb: any, statements: any, _rb: any) {
        return {
            type: 'block',
            statements: statements.children.map((s: any) => s.parse())
        } as ast.Block;
    },

    Conditional(_if: any, _lp: any, cond: any, _rp: any, thenBranch: any, _else: any, elseBranch: any) {
        return {
            type: 'if',
            condition: cond.parse(),
            thenBranch: thenBranch.parse(),
            elseBranch: elseBranch.children.length > 0 ? elseBranch.child(0).parse() : undefined
        } as ast.Conditional;
    },

    While(_while: any, _lp: any, cond: any, _rp: any, _inv: any, inv: any, body: any) {
        return {
            type: 'while',
            condition: cond.parse(),
            body: body.parse()
        } as ast.While;
    },

    Assignment_simple(target: any, _eq: any, value: any, _semi: any) {
        return {
            type: 'assign',
            kind: 'simple',
            targets: [target.sourceString],
            value: value.parse()
        } as ast.Assignment;
    },

    Assignment_array(name: any, _lb: any, index: any, _rb: any, _eq: any, value: any, _semi: any) {
        return {
            type: 'assign',
            kind: 'array',
            targets: [name.sourceString],
            indices: [index.parse()],
            value: value.parse()
        } as ast.Assignment;
    },

    Assignment_tuple(first: any, _commas: any, rest: any, _eq: any, call: any, _semi: any) {
        return {
            type: 'assign',
            kind: 'tuple',
            targets: [first.sourceString, ...rest.children.map((n: any) => n.sourceString)],
            value: call.parse()
        } as ast.Assignment;
    },

    OrCondition_or(left: any, _or: any, right: any) {
        return {
            type: 'binCond',
            op: 'or',
            left: left.parse(),
            right: right.parse()
        } as ast.BinaryCondition;
    },

    AndCondition_and(left: any, _and: any, right: any) {
        return {
            type: 'binCond',
            op: 'and',
            left: left.parse(),
            right: right.parse()
        } as ast.BinaryCondition;
    },

    ImpliesCondition_implies(left: any, _arrow: any, right: any) {
        return {
            type: 'binCond',
            op: '->',
            left: left.parse(),
            right: right.parse()
        } as ast.BinaryCondition;
    },

    NotCondition_not(_not: any, cond: any) {
        return {
            type: 'not',
            argument: cond.parse()
        } as ast.NotCondition;
    },

    PrimaryCondition_true(_true: any) {
        return {
            type: 'bool',
            value: true
        } as ast.BoolLiteral;
    },

    PrimaryCondition_false(_false: any) {
        return {
            type: 'bool',
            value: false
        } as ast.BoolLiteral;
    },

    PrimaryCondition_comp(comp: any) {
        return comp.parse();
    },

    PrimaryCondition_paren(_lp: any, cond: any, _rp: any) {
        return cond.parse();
    },

    Comparison(left: any, op: any, right: any) {
        return {
            type: 'comp',
            op: op.sourceString as '==' | '!=' | '<' | '<=' | '>' | '>=',
            left: left.parse(),
            right: right.parse()
        } as ast.Comparison;
    },

    FunctionCall(name: any, _lp: any, args: any, _rp: any) {
        return {
            type: 'call',
            name: name.sourceString,
            args: args.asIteration().children.map((a: any) => a.parse())
        } as ast.FunctionCall;
    },

    PrimaryExpr_call(call: any) {
        return call.parse();
    },

    PrimaryExpr_array(access: any) {
        return access.parse();
    },

    ArrayAccess(name: any, _lb: any, index: any, _rb: any) {
        return {
            type: 'arrayAccess',
            name: name.sourceString,
            index: index.parse()
        } as ast.ArrayAccess;
    },

    Expr: getExprAst.Expr,
    AddExpr: getExprAst.AddExpr,
    MulExpr: getExprAst.MulExpr,
    UnaryExpr_neg: getExprAst.UnaryExpr_neg,
    UnaryExpr_pos: getExprAst.UnaryExpr_pos,
    PrimaryExpr_paren: getExprAst.PrimaryExpr_paren,
    PrimaryExpr_num: getExprAst.PrimaryExpr_num,
    PrimaryExpr_var: getExprAst.PrimaryExpr_var,
} satisfies FunnyActionDict<any>;

export const semantics: FunnySemanticsExt = grammar.Funny.createSemantics() as FunnySemanticsExt;
semantics.addOperation("parse()", getFunnyAst);

export interface FunnySemanticsExt extends Semantics {
    (match: MatchResult): FunnyActionsExt
}
interface FunnyActionsExt {
    parse(): ast.Module;
}

export function parseFunny(source: string): ast.Module {
    const match = grammar.Funny.match(source, 'Module');
    if (match.failed()) {
        const interval = match.getInterval();
        throw new FunnyError(
            match.message || "Syntax error",
            "SyntaxError",
            interval.getLineAndColumn().lineNum,
            interval.getLineAndColumn().colNum
        );
    }
    const module = (semantics(match) as FunnyActionsExt).parse();
    validateSemantics(module, source);
    return module;
}

function validateSemantics(module: ast.Module, source: string) {
    const functionMap = new Map<string, ast.FunctionDef>();
    for (const func of module.functions) { // Валидация уникальности функций
        if (functionMap.has(func.name)) {
            throw new FunnyError(
                `Function '${func.name}' is already defined`,
                "DuplicateFunction"
            );
        }
        functionMap.set(func.name, func);
        const varMap = new Map<string, { type: 'param' | 'return' | 'local', varType: ast.VarType, used: boolean }>();
        for (const param of func.parameters) { // Проверка параметров функции
            if (varMap.has(param.name)) {
                const pos = getPosition(source, param.name);
                throw new FunnyError(
                    `Parameter '${param.name}' is already declared`,
                    "VariableRedefinition",
                    pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
                );
            }
            varMap.set(param.name, { type: 'param', varType: param.varType, used: false });
        }
        for (const ret of func.returns) { // Проверка возвращаемых значений
            if (varMap.has(ret.name)) {
                const pos = getPosition(source, ret.name);
                throw new FunnyError(
                    `Return value '${ret.name}' is already declared`,
                    "VariableRedefinition",
                    pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
                );
            }
            varMap.set(ret.name, { type: 'return', varType: ret.varType, used: false });
        }
        for (const local of func.locals) { // Проверка локальных переменных
            if (varMap.has(local.name)) {
                const pos = getPosition(source, local.name);
                throw new FunnyError(
                    `Local variable '${local.name}' is already declared`,
                    "VariableRedefinition",
                    pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
                );
            }
            varMap.set(local.name, { type: 'local', varType: local.varType, used: false });
        }
        validateStatement(func.body, varMap, functionMap, func.parameters, source); // Рекурсивная проверка тела функции
    }
}

function validateStatement( // рекурсивная валидация операторов
    stmt: ast.Statement, 
    varMap: Map<string, { type: 'param' | 'return' | 'local', varType: ast.VarType, used: boolean }>,
    functionMap: Map<string, ast.FunctionDef>,
    params: ast.ParameterDef[],
    source: string
) {
    switch (stmt.type) {
        case 'assign':
            validateAssignment(stmt, varMap, functionMap, params, source);
            break;
        case 'block':
            for (const s of stmt.statements) {
                validateStatement(s, varMap, functionMap, params, source);
            }
            break;
        case 'if':
            validateCondition(stmt.condition, varMap, source);
            validateStatement(stmt.thenBranch, varMap, functionMap, params, source);
            if (stmt.elseBranch) {
                validateStatement(stmt.elseBranch, varMap, functionMap, params, source);
            }
            break;
        case 'while':
            validateCondition(stmt.condition, varMap, source);
            validateStatement(stmt.body, varMap, functionMap, params, source);
            break;
    }
}

function validateAssignment( // валидация присваиваний
    assign: ast.Assignment,
    varMap: Map<string, { type: 'param' | 'return' | 'local', varType: ast.VarType, used: boolean }>,
    functionMap: Map<string, ast.FunctionDef>,
    params: ast.ParameterDef[],
    source: string
) {
    if (assign.kind === 'simple' || assign.kind === 'array') {
        const target = assign.targets[0]; // Проверка существования переменной
        const varInfo = varMap.get(target);
        if (!varInfo) {
            const pos = getPosition(source, target);
            throw new FunnyError(
                `Undeclared identifier '${target}'`,
                "UndeclaredIdentifier",
                pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
            );
        }
        if (varInfo.type === 'param') { // Запрет присваивания параметрам
            const pos = getPosition(source, target);
            throw new FunnyError(
                `Cannot assign to parameter '${target}'`,
                "AssignToParameter",
                pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
            );
        }
        if (assign.kind === 'array') { // Проверка типа массива
            if (varInfo.varType !== 'int[]') {
                const pos = getPosition(source, target);
                throw new FunnyError(
                    `Cannot index non-array variable '${target}'`,
                    "TypeMismatch",
                    pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
                );
            }
            if (assign.indices) { // Валидация индексного выражения
                validateExpr(assign.indices[0], varMap, functionMap, source);
            }
        }
        if (assign.value.type === 'call') { // Валидация правой части присваивания
            validateFunctionCall(assign.value, varMap, functionMap, source, true);
        } else {
            validateExpr(assign.value as arith.Expr, varMap, functionMap, source);
        }
    } else if (assign.kind === 'tuple') {
        for (const target of assign.targets) { // Проверка всех целевых переменных
            const varInfo = varMap.get(target);
            if (!varInfo) {
                const pos = getPosition(source, target);
                throw new FunnyError(
                    `Undeclared identifier '${target}'`,
                    "UndeclaredIdentifier",
                    pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
                );
            }
            if (varInfo.type === 'param') {
                const pos = getPosition(source, target);
                throw new FunnyError(
                    `Cannot assign to parameter '${target}'`,
                    "AssignToParameter",
                    pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
                );
            }
        }
        if (assign.value.type === 'call') { // Проверка вызываемой функции
            const call = assign.value as ast.FunctionCall;
            const func = functionMap.get(call.name);
            if (!func) {
                const pos = getPosition(source, call.name);
                throw new FunnyError(
                    `Undeclared function '${call.name}'`,
                    "UndeclaredFunction",
                    pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
                );
            }
            if (func.returns.length !== assign.targets.length) { // Проверка соответствия количества значений
                throw new FunnyError(
                    `Function '${call.name}' returns ${func.returns.length} value(s), but ${assign.targets.length} target(s) provided`,
                    "ReturnCountMismatch"
                );
            }
            validateFunctionCall(call, varMap, functionMap, source, false);
        }
    }
}

function validateCondition(
    cond: ast.Condition,
    varMap: Map<string, { type: 'param' | 'return' | 'local', varType: ast.VarType, used: boolean }>,
    source: string
) {
    switch (cond.type) {
        case 'bool':
            break;
        case 'comp':
            validateExpr(cond.left, varMap, new Map(), source);
            validateExpr(cond.right, varMap, new Map(), source);
            break;
        case 'not':
            validateCondition(cond.argument, varMap, source);
            break;
        case 'binCond':
            validateCondition(cond.left, varMap, source);
            validateCondition(cond.right, varMap, source);
            break;
    }
}

function validateExpr(
    expr: arith.Expr | ast.ArrayAccess | ast.FunctionCall,
    varMap: Map<string, { type: 'param' | 'return' | 'local', varType: ast.VarType, used: boolean }>,
    functionMap: Map<string, ast.FunctionDef>,
    source: string
) {
    if ('type' in expr) {
        switch (expr.type) {
            case 'var':
                const varInfo = varMap.get(expr.name);
                if (!varInfo) {
                    const pos = getPosition(source, expr.name);
                    throw new FunnyError(
                        `Undeclared identifier '${expr.name}'`,
                        "UndeclaredIdentifier",
                        pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
                    );
                }
                varInfo.used = true;
                break;
            case 'arrayAccess':
                const arrayVar = varMap.get(expr.name);
                if (!arrayVar) {
                    const pos = getPosition(source, expr.name);
                    throw new FunnyError(
                        `Undeclared identifier '${expr.name}'`,
                        "UndeclaredIdentifier",
                        pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
                    );
                }
                arrayVar.used = true;
                validateExpr(expr.index, varMap, functionMap, source); // Рекурсивно проверяем индекс
                break;
            case 'call':
                validateFunctionCall(expr, varMap, functionMap, source);
                break;
            case 'binary':
                validateExpr(expr.left, varMap, functionMap, source);
                validateExpr(expr.right, varMap, functionMap, source);
                break;
            case 'neg':
                validateExpr(expr.argument, varMap, functionMap, source);
                break;
        }
    }
}

function validateFunctionCall(
    call: ast.FunctionCall,
    varMap: Map<string, { type: 'param' | 'return' | 'local', varType: ast.VarType, used: boolean }>,
    functionMap: Map<string, ast.FunctionDef>,
    source: string,
    inExpression: boolean = true
) {
    if (call.name === 'length') {
        if (call.args.length !== 1) {
            throw new FunnyError(
                `Function 'length' expects 1 argument, got ${call.args.length}`,
                "ArgumentCountMismatch"
            );
        }
        validateExpr(call.args[0], varMap, functionMap, source);
        return;
    }
    const func = functionMap.get(call.name);
    if (!func) { // Существование функции
        const pos = getPosition(source, call.name);
        throw new FunnyError(
            `Undeclared function '${call.name}'`,
            "UndeclaredFunction",
            pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
        );
    }
    if (inExpression && func.returns.length !== 1) { // Проверка возвращаемых значений
        throw new FunnyError(
            `Function '${call.name}' returns ${func.returns.length} values, cannot be used in expression`,
            "ReturnCountMismatch"
        );
    }
    if (func.parameters.length !== call.args.length) { // Проверка количества аргументов
        throw new FunnyError(
            `Function '${call.name}' expects ${func.parameters.length} argument(s), got ${call.args.length}`,
            "ArgumentCountMismatch"
        );
    }
    for (const arg of call.args) { // Рекурсивная проверка аргументов
        validateExpr(arg, varMap, functionMap, source);
    }
}

function getPosition(source: string, identifier: string): { startLine: number, startCol: number, endCol: number, endLine: number } | null {
    const lines = source.split('\n');
    for (let lineNum = 0; lineNum < lines.length; lineNum++) {
        const line = lines[lineNum];
        const idx = line.indexOf(identifier);
        if (idx !== -1) {
            return {
                startLine: lineNum + 1,
                startCol: idx + 1,
                endCol: idx + identifier.length + 1,
                endLine: lineNum + 1
            };
        }
    }
    return null;
} 
