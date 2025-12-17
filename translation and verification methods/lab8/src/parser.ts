import { getExprAst } from '../../lab04';
import * as ast from './funny';
import * as arith from '../../lab04';
import { FunnyError, FunnyWarning } from './index';

import grammar, { FunnyActionDict } from './funny.ohm-bundle';

import { MatchResult, Semantics, Node } from 'ohm-js';

let warnings: FunnyWarning[] = [];

export const getFunnyAst = {
    //парсит модуль, который состоит из одной или нескольких функций
    Module(functions: any) {
        return {
            type: 'module',
            functions: functions.children.map((f: any) => f.parse())
        } as ast.Module;
    },

    //парсит определение функции с параметрами, возвращаемыми значениями, локальными переменными и телом
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

    //парсит список параметров функции (разделенных запятыми)
    ParameterList(first: any, _commas: any, rest: any) {
        return [first.parse(), ...rest.children.map((n: any) => n.parse())];
    },

    //парсит список локальных переменных (разделенных запятыми)
    LocalsList(first: any, _commas: any, rest: any) {
        return [first.parse(), ...rest.children.map((n: any) => n.parse())];
    },

    //парс определение переменной с именем и типом
    VariableDef(name: any, _colon: any, type: any) {
        return {
            type: 'param',
            name: name.sourceString,
            varType: type.parse()
        } as ast.ParameterDef;
    },

    //парс определение локальной 
    LocalDef(name: any, _colon: any, _int: any) {
        return {
            type: 'param',
            name: name.sourceString,
            varType: 'int'
        } as ast.ParameterDef;
    },

    //парс массива 
    Type_array(_int: any, _lb: any) {
        return 'int[]' as ast.VarType;
    },

    //парс числа
    Type_int(_int: any) {
        return 'int' as ast.VarType;
    },

    //парс блока операторов в {}
    Block(_lb: any, statements: any, _rb: any) {
        return {
            type: 'block',
            statements: statements.children.map((s: any) => s.parse())
        } as ast.Block;
    },

    //парс if
    Conditional(_if: any, _lp: any, cond: any, _rp: any, thenBranch: any, _else: any, elseBranch: any) {
        return {
            type: 'if',
            condition: cond.parse(),
            thenBranch: thenBranch.parse(),
            elseBranch: elseBranch.children.length > 0 ? elseBranch.child(0).parse() : undefined
        } as ast.Conditional;
    },

    //
    While(_while: any, _lp: any, cond: any, _rp: any, _inv: any, inv: any, body: any) {
        return {
            type: 'while',
            condition: cond.parse(),
            body: body.parse()
        } as ast.While;
    },

    //парс простого присваивания x = выраж
    Assignment_simple(target: any, _eq: any, value: any, _semi: any) {
        return {
            type: 'assign',
            kind: 'simple',
            targets: [target.sourceString],
            value: value.parse()
        } as ast.Assignment;
    },

    //парс присв элементу массива arr[index] = выраж
    Assignment_array(name: any, _lb: any, index: any, _rb: any, _eq: any, value: any, _semi: any) {
        return {
            type: 'assign',
            kind: 'array',
            targets: [name.sourceString],
            indices: [index.parse()],
            value: value.parse()
        } as ast.Assignment;
    },

    //кортеж x, y, z = func()
    Assignment_tuple(first: any, _commas: any, rest: any, _eq: any, call: any, _semi: any) {
        return {
            type: 'assign',
            kind: 'tuple',
            targets: [first.sourceString, ...rest.children.map((n: any) => n.sourceString)],
            value: call.parse()
        } as ast.Assignment;
    },

    //or
    OrCondition_or(left: any, _or: any, right: any) {
        return {
            type: 'binCond',
            op: 'or',
            left: left.parse(),
            right: right.parse()
        } as ast.BinaryCondition;
    },

    //and
    AndCondition_and(left: any, _and: any, right: any) {
        return {
            type: 'binCond',
            op: 'and',
            left: left.parse(),
            right: right.parse()
        } as ast.BinaryCondition;
    },

    //->
    ImpliesCondition_implies(left: any, _arrow: any, right: any) {
        return {
            type: 'binCond',
            op: '->',
            left: left.parse(),
            right: right.parse()
        } as ast.BinaryCondition;
    },

    //not
    NotCondition_not(_not: any, cond: any) {
        return {
            type: 'not',
            argument: cond.parse()
        } as ast.NotCondition;
    },

    //true
    PrimaryCondition_true(_true: any) {
        return {
            type: 'bool',
            value: true
        } as ast.BoolLiteral;
    },

    //false
    PrimaryCondition_false(_false: any) {
        return {
            type: 'bool',
            value: false
        } as ast.BoolLiteral;
    },

    //условие сравнения
    PrimaryCondition_comp(comp: any) {
        return comp.parse();
    },

    //условие в скобках
    PrimaryCondition_paren(_lp: any, cond: any, _rp: any) {
        return cond.parse();
    },

    //операции сравнения
    Comparison(left: any, op: any, right: any) {
        return {
            type: 'comp',
            op: op.sourceString as '==' | '!=' | '<' | '<=' | '>' | '>=',
            left: left.parse(),
            right: right.parse()
        } as ast.Comparison;
    },

    //функция с аргументами
    FunctionCall(name: any, _lp: any, args: any, _rp: any) {
        return {
            type: 'call',
            name: name.sourceString,
            args: args.asIteration().children.map((a: any) => a.parse())
        } as ast.FunctionCall;
    },

    //вызов функции как первичное выржаение 
    PrimaryExpr_call(call: any) {
        return call.parse();
    },

    //доступ к элементу массива как первичное выражение 
    PrimaryExpr_array(access: any) {
        return access.parse();
    },

    //вещественные числа не поддерживаются
    PrimaryExpr_float(floatNum: any) {
        const interval = floatNum.source;
        const pos = interval.getLineAndColumn();
        throw new FunnyError(
            `Floating point numbers are not supported: ${floatNum.sourceString}`,
            "FloatNotSupported",
            pos.lineNum,
            pos.colNum
        );
    },

    //обращение по индексу
    ArrayAccess(name: any, _lb: any, index: any, _rb: any) {
        return {
            type: 'arrayAccess',
            name: name.sourceString,
            index: index.parse()
        } as ast.ArrayAccess;
    },

    ...getExprAst
} satisfies FunnyActionDict<any>;

//обьект семантики для фанни
export const semantics: FunnySemanticsExt = grammar.Funny.createSemantics() as FunnySemanticsExt;
//добавляем parse
semantics.addOperation("parse()", getFunnyAst);

export interface FunnySemanticsExt extends Semantics
{
    (match: MatchResult): FunnyActionsExt
}
interface FunnyActionsExt 
{
    parse(): ast.Module;
}

//принимает код на фанни и парсим в ast
export function parseFunny(source: string): ast.Module
{
    warnings = []; // Сбрасываем предупреждения
    
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
    
    // Выводим предупреждения
    if (warnings.length > 0) {
        console.warn('\nWarnings:');
        for (const warning of warnings) {
            console.warn(`  ${warning.message}`);
        }
    }
    
    return module;
}

export function getWarnings(): FunnyWarning[] {
    return warnings;
}

//проверяем модуль на повторные определения, незадекл идентификаторы и соотв типов
function validateSemantics(module: ast.Module, source: string) {
    const functionMap = new Map<string, ast.FunctionDef>();
    
    for (const func of module.functions) {
        if (functionMap.has(func.name)) {
            throw new FunnyError(
                `Function '${func.name}' is already defined`,
                "DuplicateFunction"
            );
        }
        functionMap.set(func.name, func);
        
        const varMap = new Map<string, { type: 'param' | 'return' | 'local', varType: ast.VarType, used: boolean }>();
        
        for (const param of func.parameters) {
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
        
        for (const ret of func.returns) {
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
        
        for (const local of func.locals) {
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
        
        validateStatement(func.body, varMap, functionMap, func.parameters, source);
        
        // Проверяем неиспользуемые параметры и локальные переменные
        for (const [name, info] of varMap.entries()) {
            if (!info.used) {
                const pos = getPosition(source, name);
                if (info.type === 'param') {
                    warnings.push(new FunnyWarning(
                        `Parameter '${name}' is declared but never used in function '${func.name}'`,
                        "UnusedParameter",
                        pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
                    ));
                } else if (info.type === 'local') {
                    warnings.push(new FunnyWarning(
                        `Local variable '${name}' is declared but never used in function '${func.name}'`,
                        "UnusedVariable",
                        pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
                    ));
                }
            }
        }
    }
}

//проверяем корректность операторов
function validateStatement(
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

//проверяем присваивание на существование переменных, запрет присваивания параметрам и соотв типам 
function validateAssignment(
    assign: ast.Assignment,
    varMap: Map<string, { type: 'param' | 'return' | 'local', varType: ast.VarType, used: boolean }>,
    functionMap: Map<string, ast.FunctionDef>,
    params: ast.ParameterDef[],
    source: string
) {
    if (assign.kind === 'simple' || assign.kind === 'array') {
        const target = assign.targets[0];
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
        
        if (assign.kind === 'array') {
            if (varInfo.varType !== 'int[]') {
                const pos = getPosition(source, target);
                throw new FunnyError(
                    `Cannot index non-array variable '${target}'`,
                    "TypeMismatch",
                    pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
                );
            }
            if (assign.indices) {
                validateExpr(assign.indices[0], varMap, functionMap, source);
            }
        }
        
        if (assign.value.type === 'call') {
            const call = assign.value as ast.FunctionCall;
            validateFunctionCall(call, varMap, functionMap, source, true);
            // Проверка типов для simple assignment с вызовом функции
            const func = functionMap.get(call.name);
            if (func && func.returns.length === 1 && assign.kind === 'simple') {
                const returnType = func.returns[0].varType;
                if (varInfo.varType !== returnType) {
                    const pos = getPosition(source, target);
                    throw new FunnyError(
                        `Type mismatch: cannot assign '${returnType}' to '${varInfo.varType}'`,
                        "TypeMismatch",
                        pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
                    );
                }
            }
        } else {
            validateExpr(assign.value as arith.Expr, varMap, functionMap, source);
        }
    } else if (assign.kind === 'tuple') {
        for (const target of assign.targets) {
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
        
        if (assign.value.type === 'call') {
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
            // Проверка количества параметров ПЕРЕД проверкой типов
            if (func.parameters.length !== call.args.length) {
                throw new FunnyError(
                    `Function '${call.name}' expects ${func.parameters.length} argument(s), got ${call.args.length}`,
                    "ArgumentCountMismatch"
                );
            }
            if (func.returns.length !== assign.targets.length) {
                throw new FunnyError(
                    `Function '${call.name}' returns ${func.returns.length} value(s), but ${assign.targets.length} target(s) provided`,
                    "ReturnCountMismatch"
                );
            }
            // Проверка типов для tuple assignment
            for (let i = 0; i < assign.targets.length; i++) {
                const targetVar = varMap.get(assign.targets[i]);
                const returnType = func.returns[i].varType;
                if (targetVar && targetVar.varType !== returnType) {
                    const pos = getPosition(source, assign.targets[i]);
                    throw new FunnyError(
                        `Type mismatch: cannot assign '${returnType}' to '${targetVar.varType}'`,
                        "TypeMismatch",
                        pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
                    );
                }
            }
            // Проверяем аргументы
            for (const arg of call.args) {
                validateExpr(arg, varMap, functionMap, source);
            }
        }
    }
}

//проверяем логическое условие (корректность всех подвыражений)
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

//проверяем арифм выражение на исп переменных, доступ к массива и вызовы функций
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
                validateExpr(expr.index, varMap, functionMap, source);
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

//проверям вызов функции на существование, соотв количества и типов аргументов
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
    if (!func) {
        const pos = getPosition(source, call.name);
        throw new FunnyError(
            `Undeclared function '${call.name}'`,
            "UndeclaredFunction",
            pos?.startLine, pos?.startCol, pos?.endCol, pos?.endLine
        );
    }
    
    if (inExpression && func.returns.length !== 1) {
        throw new FunnyError(
            `Function '${call.name}' returns ${func.returns.length} values, cannot be used in expression`,
            "ReturnCountMismatch"
        );
    }
    
    if (func.parameters.length !== call.args.length) {
        throw new FunnyError(
            `Function '${call.name}' expects ${func.parameters.length} argument(s), got ${call.args.length}`,
            "ArgumentCountMismatch"
        );
    }
    
    for (const arg of call.args) {
        validateExpr(arg, varMap, functionMap, source);
    }
}

//находим поцизию идентификатора в исх коде (точное место ошибки)
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
