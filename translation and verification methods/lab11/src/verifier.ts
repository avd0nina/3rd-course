import { Arith, Bool, Context, init } from "z3-solver";

import { printFuncCall } from "./printFuncCall";
import { AnnotatedModule, FunctionDef, Predicate, While } from "../../lab10";
import { Statement, Assignment, Block, Conditional, FunctionCall } from "../../lab08";
import * as arith from "../../lab04";

let z3anchor: any;

async function initZ3() {
    if (!z3) {
        z3anchor = await init();
        const Z3C = z3anchor.Context;
        z3 = Z3C('main');
    }
}

export function flushZ3() {
    z3anchor = undefined;
    z3 = undefined as any;
    z3Functions.clear();
}

let z3: Context;
const z3Functions = new Map<string, any>();

// типы условий верификации для точного указания места ошибки 
export type ConditionType = 'precondition' | 'postcondition' | 'loop_invariant_init' | 'loop_invariant_preserve' | 'loop_invariant_exit' | 'function_call_requires' | 'array_bounds';

// результат верификации при ошибке с подробной информацией
export interface VerificationFailure {
    valid: false;
    message: string;
    conditionType: ConditionType;
    condition?: Predicate;
    location: {
        funcName: string;
        statementType?: string;
        details?: string;
    };
    counterexample?: string;
}

// результат успешной верификации
export interface VerificationSuccess {
    valid: true;
}

export type VerificationResult = VerificationSuccess | VerificationFailure;

// условие верификации с метаданными о его происхождении
interface VerificationCondition {
    predicate: Predicate;
    conditionType: ConditionType;
    details?: string;
}

// исключение верификации с подробной информацией о месте ошибки
export class VerificationError extends Error {
    constructor(
        message: string,
        public funcName: string,
        public locationType?: string,
        public conditionType?: ConditionType,
        public counterexample?: string,
        public details?: string
    ) {
        super(message);
        this.name = 'VerificationError';
    }
}

// описание runtime проверки для вставки в wasm код
export interface RuntimeCheck {
    condition: Predicate;
    errorMessage: string;
    conditionType: ConditionType;
}

let runtimeChecks: RuntimeCheck[] = [];

// возвращает список runtime проверок
export function getRuntimeChecks(): RuntimeCheck[] {
    return runtimeChecks;
}

export function clearRuntimeChecks(): void {
    runtimeChecks = [];
}

// верификация всего модуля
export async function verifyModule(module: AnnotatedModule) {
    await initZ3();
    clearRuntimeChecks();
    for (const func of module.functions) {
        await verifyFunction(func, module);
    }
}

// верификация одной функции
async function verifyFunction(func: FunctionDef, module: AnnotatedModule) {
    const vcs = buildFunctionVerificationConditionsDetailed(func, module); // построй условия проверки для функции
    for (const vc of vcs) {
        if (vc.predicate.type === 'bool' && (vc.predicate as any).value === true) { // если условие просто говорит 'всегда правда', то пропускаем проверку
            continue;
        }
        const result = await proveTheoremDetailed(vc, func, module); // подожди, пока докажется теорема
        if (!result.valid) {
            throw new VerificationError( // верификация провалилась - выбрасываем ошибку с деталями
                `Verification failed for function ${func.name}: ${result.message}`,
                func.name,
                result.location.statementType,
                result.conditionType,
                result.counterexample,
                result.location.details
            );
        }
    }
}

// построение условий верификации
function buildFunctionVerificationConditionsDetailed(func: FunctionDef, module: AnnotatedModule): VerificationCondition[] {
    const conditions: VerificationCondition[] = [];
    const requires: Predicate = func.requires || { type: 'bool', value: true }; // предусловие 
    const ensures: Predicate = func.ensures || { type: 'bool', value: true }; // постусловие
    const bodyConditions = computeWPDetailed(func.body, ensures, func, module); // вычисли самое слабое предусловие
    for (const bc of bodyConditions) {
        conditions.push({
            predicate: {
                type: 'binPred',
                op: '->', // если ..., то ...
                left: requires, // левая часть (требования)
                right: bc.predicate // правая часть (самое слабое предусловие)
            }, // ЕСЛИ требования выполнены, ТО самое слабое предусловие истинно
            conditionType: bc.conditionType,
            details: bc.details
        });
    }
    return conditions;
}

// вычисление wp
function computeWPDetailed(stmt: Statement, post: Predicate, func: FunctionDef, module: AnnotatedModule): VerificationCondition[] {
    switch (stmt.type) {
        case 'block':
            return computeWPBlockDetailed(stmt as Block, post, func, module);
        case 'assign':
            return computeWPAssignmentDetailed(stmt as Assignment, post, func, module);
        case 'if':
            return computeWPConditionalDetailed(stmt as Conditional, post, func, module);
        case 'while':
            return computeWPWhileDetailed(stmt as While, post, func, module);
        default:
            return [{ predicate: post, conditionType: 'postcondition' }];
    }
}

// обработка блока
function computeWPBlockDetailed(block: Block, post: Predicate, func: FunctionDef, module: AnnotatedModule): VerificationCondition[] {
    let currentConditions: VerificationCondition[] = [{ predicate: post, conditionType: 'postcondition' }];
    //идём с конца блока к началу
    for (let i = block.statements.length - 1; i >= 0; i--) { // каждое присваивание меняет значение переменных, и нам нужно "пройти назад", чтобы понять, какие должны быть исходные значения
        const stmt = block.statements[i]; // берем текущий оператор
        const newConditions: VerificationCondition[] = []; // создаем пустой массив для НОВЫХ условий
        for (const cond of currentConditions) { // это условия, которые должны быть ПОСЛЕ текущего оператора
            const stmtConds = computeWPDetailed(stmt, cond.predicate, func, module); // что должно быть ДО выполнения оператора stmt, чтобы ПОСЛЕ него было условие cond.predicate
            newConditions.push(...stmtConds);
        }
        currentConditions = newConditions;
    }
    return currentConditions;
}

// обработка присваиваний
function computeWPAssignmentDetailed(assign: Assignment, post: Predicate, func: FunctionDef, module: AnnotatedModule): VerificationCondition[] {
    if (assign.value.type === 'call') { // правая часть - вызов функции
        const call = assign.value as FunctionCall;
        const calledFunc = module.functions.find(f => f.name === call.name); // ищем функцию по имени в модуле
        if (calledFunc) {
            const conditions: VerificationCondition[] = [];
            // проверка предусловия вызываемой функции
            let calledRequires = calledFunc.requires || { type: 'bool', value: true };
            calledRequires = substituteCallArgs(calledRequires, calledFunc, call);
            conditions.push({
                predicate: calledRequires,
                conditionType: 'function_call_requires',
                details: `Call to function '${call.name}'`
            });
            // цикл замены переменных
            let result = post;
            for (let i = assign.targets.length - 1; i >= 0; i--) { // идем с конца массива
                const target = assign.targets[i]; // target - массив переменных, которым присваиваются результаты
                const returnVar = calledFunc.returns[i];  // returns - массив описаний возвращаемых значений функции
                const substitutedExpr: arith.Expr = { type: 'var', name: `${call.name}_ret_${returnVar.name}` }; // создается временная переменная для результата функции
                result = substitutePredicate(result, target, substitutedExpr); // берем предикат result, находим все вхождения переменной target, заменяем их на substitutedExpr
            }
            // подставляем аргументы в ensures вызываемой функции
            let calledEnsures = calledFunc.ensures || { type: 'bool', value: true };
            calledEnsures = substituteCallArgs(calledEnsures, calledFunc, call);
            // переименовываем возвращаемые переменные на свежие имена
            for (let i = 0; i < calledFunc.returns.length; i++) {
                const returnName = calledFunc.returns[i].name;
                const freshName = `${call.name}_ret_${returnName}`;
                calledEnsures = renameVariable(calledEnsures, returnName, freshName);
            }
            conditions.push({
                predicate: { type: 'binPred', op: '->', left: calledEnsures, right: result },
                conditionType: 'postcondition',
                details: `After call to function '${call.name}'`
            }); // требования функции выполнены И (если гарантии функции истинны, то наше условие истинно)
            return conditions;
        }
    }
    if (assign.kind === 'simple' && assign.targets.length === 1) { // простое присваивание одной переменной
        return [{
            predicate: substitutePredicate(post, assign.targets[0], assign.value as arith.Expr), // заменяет все вхождения переменной в условии на выражение
            conditionType: 'postcondition',
            details: `Assignment to '${assign.targets[0]}'`
        }];
    }
    if (assign.kind === 'array') { // присваивание в массив
        const target = assign.targets[0]; // имя массива
        const index = assign.indices?.[0]; // берем первый индекс
        const value = assign.value as arith.Expr; // значение для присваивания
        if (index) {
            const conditions: VerificationCondition[] = []; // создаем массив условий
            //проверка границ массива: 0 <= index < length(arr)
            const boundsCheck: Predicate = {
                type: 'binPred',
                op: 'and',
                left: {
                    type: 'comp',
                    op: '>=',
                    left: index,
                    right: { type: 'num', value: 0 }
                }, // индекс не должен быть отрицательным
                right: {
                    type: 'comp',
                    op: '<',
                    left: index,
                    right: { type: 'call', name: 'length', args: [{ type: 'var', name: target }] } as any
                } // индекс должен быть меньше длины массива
            };
            conditions.push({
                predicate: boundsCheck,
                conditionType: 'array_bounds',
                details: `Array bounds check for '${target}[...]'`
            });
            // подставляем значение в предикат для всех обращений arr[i]
            const updatedPost = substituteArrayAccess(post, target, index, value); // найди в условии post все обращения arr[index] и замени их на value
            conditions.push({
                predicate: updatedPost,
                conditionType: 'postcondition',
                details: `Array assignment '${target}[...] = ...'`
            });
            return conditions;
        }
    }
    return [{ predicate: post, conditionType: 'postcondition' }];
}

// подставляет значение вместо arr[index] в предикате
function substituteArrayAccess(pred: Predicate, arrayName: string, index: arith.Expr, value: arith.Expr): Predicate {
    switch (pred.type) {
        case 'bool': return pred; // просто возвращает как есть
        case 'comp': return {
            type: 'comp',
            op: pred.op,
            left: substituteArrayAccessExpr(pred.left, arrayName, index, value),
            right: substituteArrayAccessExpr(pred.right, arrayName, index, value)
        };
        case 'not': return { type: 'not', argument: substituteArrayAccess(pred.argument, arrayName, index, value) };
        case 'binPred': return {
            type: 'binPred',
            op: pred.op,
            left: substituteArrayAccess(pred.left, arrayName, index, value),
            right: substituteArrayAccess(pred.right, arrayName, index, value)
        };
        case 'quantifier': return {
            type: 'quantifier',
            quantifier: pred.quantifier,
            variable: pred.variable,
            body: substituteArrayAccess(pred.body, arrayName, index, value)
        };
        case 'formulaRef': return {
            type: 'formulaRef',
            name: pred.name,
            args: pred.args.map(arg => substituteArrayAccessExpr(arg, arrayName, index, value))
        };
        default: return pred;
    }
}

//подставляет значение вместо arr[index] в выражении
function substituteArrayAccessExpr(e: arith.Expr | any, arrayName: string, index: arith.Expr, value: arith.Expr): arith.Expr {
    switch (e.type) {
        case 'num': return e;
        case 'var': return e;
        case 'binary': return {
            type: 'binary',
            op: e.op,
            left: substituteArrayAccessExpr(e.left, arrayName, index, value),
            right: substituteArrayAccessExpr(e.right, arrayName, index, value)
        };
        case 'neg': return { type: 'neg', argument: substituteArrayAccessExpr(e.argument, arrayName, index, value) };
        case 'arrayAccess':
            //если это тот самый доступ к массиву - заменяем на value
            if (e.name === arrayName && exprsEqual(e.index, index)) {
                return value; // замена
            }
            return { // если это не тот массив/индекс, все равно рекурсивно проверяем индекс, потому что индекс сам может содержать обращения к массивам
                type: 'arrayAccess',
                name: e.name,
                index: substituteArrayAccessExpr(e.index, arrayName, index, value)
            } as any;
        case 'call': return {
            type: 'call',
            name: e.name,
            args: e.args.map((arg: any) => substituteArrayAccessExpr(arg, arrayName, index, value))
        } as any;
        default: return e;
    }
}

// проверяет синтаксическое равенство двух выражений
function exprsEqual(a: arith.Expr | any, b: arith.Expr | any): boolean {
    if (a.type !== b.type) return false;
    switch (a.type) {
        case 'num': return a.value === b.value;
        case 'var': return a.name === b.name;
        case 'binary': return a.op === b.op && exprsEqual(a.left, b.left) && exprsEqual(a.right, b.right);
        case 'neg': return exprsEqual(a.argument, b.argument);
        default: return false;
    }
}

// обрабокта условий
function computeWPConditionalDetailed(cond: Conditional, post: Predicate, func: FunctionDef, module: AnnotatedModule): VerificationCondition[] {
    const condPred = conditionToPredicate(cond.condition); // преобразует условие if в логический предикат
    const thenConditions = computeWPDetailed(cond.thenBranch, post, func, module); // что должно быть истинно ПЕРЕД выполнением ветки then, чтобы ПОСЛЕ нее было условие post
    const conditions: VerificationCondition[] = []; // создаем массив результатов
    for (const tc of thenConditions) {
        conditions.push({
            predicate: { type: 'binPred', op: '->', left: condPred, right: tc.predicate },
            conditionType: tc.conditionType,
            details: `Then branch: ${tc.details || ''}`
        }); // ЕСЛИ условие if истинно, ТО должно выполняться условие для ветки then
    }
    if (cond.elseBranch) {
        const elseConditions = computeWPDetailed(cond.elseBranch, post, func, module); // аналогично wpThen
        for (const ec of elseConditions) {
            conditions.push({
                predicate: { type: 'binPred', op: '->', left: { type: 'not', argument: condPred }, right: ec.predicate },
                conditionType: ec.conditionType,
                details: `Else branch: ${ec.details || ''}`
            }); // ЕСЛИ условие if ложно, ТО должно выполняться условие для ветки else
        }
    } else { // нет else
        conditions.push({
            predicate: { type: 'binPred', op: '->', left: { type: 'not', argument: condPred }, right: post },
            conditionType: 'postcondition',
            details: 'No else branch'
        }); // ЕСЛИ условие if ложно (ветка then не выполняется), ТО должно выполняться исходное условие post
    }
    return conditions;
}

// обрабокта цикла
function computeWPWhileDetailed(whileStmt: While, post: Predicate, func: FunctionDef, module: AnnotatedModule): VerificationCondition[] {
    const inv = whileStmt.invariant || { type: 'bool', value: true }; // условие, которое всегда истинно в определенной точке цикла
    const condPred = conditionToPredicate(whileStmt.condition); // преобразуем условие цикла в предикат
    const modifiedVars = getModifiedVariables(whileStmt.body); // находим все переменные, которые изменяются в теле цикла
    const conditions: VerificationCondition[] = [];
    // 1. инвариант должен выполняться при входе в цикл
    conditions.push({
        predicate: inv,
        conditionType: 'loop_invariant_init',
        details: 'Loop invariant must hold on entry'
    });
    // 2. инвариант сохраняется после каждой итерации
    const bodyWP = computeWP(whileStmt.body, inv, func, module); // вычисляем наиболее слабое предусловие для тела цикла
    let preserveCheck: Predicate = {
        type: 'binPred',
        op: '->',
        left: { type: 'binPred', op: 'and', left: inv, right: condPred },
        right: bodyWP
    }; // ЕСЛИ инвариант истинен И условие цикла истинно, ТО должно выполняться wp тела цикла относительно инварианта
    // для нетривиальных инвариантов оборачиваем в forall по изменяемым переменным
    const isTrivialInv = inv.type === 'bool' && inv.value === true; // является ли инвариант тривиальным (true)
    if (!isTrivialInv) {
        for (const varName of modifiedVars) { // для каждой изменяемой переменной добавляет квантор всеобщности
            preserveCheck = {
                type: 'quantifier',
                quantifier: 'forall',
                variable: { type: 'param', name: varName, varType: 'int' },
                body: preserveCheck
            };
        }
    }
    conditions.push({
        predicate: preserveCheck,
        conditionType: 'loop_invariant_preserve',
        details: 'Loop invariant must be preserved by loop body'
    });
    // 3. после выхода из цикла
    let exitCheck: Predicate = {
        type: 'binPred',
        op: '->',
        left: { type: 'binPred', op: 'and', left: inv, right: { type: 'not', argument: condPred } },
        right: post
    }; // ЕСЛИ инвариант истинен И условие цикла ложно (цикл завершился), ТО должно выполняться постусловие
    if (!isTrivialInv) {
        for (const varName of modifiedVars) { // для каждой изменяемой переменной добавляет квантор всеобщности
            exitCheck = {
                type: 'quantifier',
                quantifier: 'forall',
                variable: { type: 'param', name: varName, varType: 'int' },
                body: exitCheck
            };
        }
    }
    conditions.push({
        predicate: exitCheck,
        conditionType: 'loop_invariant_exit',
        details: 'Loop invariant with negated condition must imply postcondition'
    });
    return conditions;
}

// пострение условий верификации (упрощённая версия)
function buildFunctionVerificationConditions(func: FunctionDef, module: AnnotatedModule): Predicate {
    const requires: Predicate = func.requires || { type: 'bool', value: true };
    const ensures: Predicate = func.ensures || { type: 'bool', value: true };
    const wp = computeWP(func.body, ensures, func, module);
    return {
        type: 'binPred',
        op: '->',
        left: requires,
        right: wp
    };
}

// вычисление wp (упрощённая версия)
function computeWP(stmt: Statement, post: Predicate, func: FunctionDef, module: AnnotatedModule): Predicate {
    switch (stmt.type) {
        case 'block':
            return computeWPBlock(stmt as Block, post, func, module);
        case 'assign':
            return computeWPAssignment(stmt as Assignment, post, func, module);
        case 'if':
            return computeWPConditional(stmt as Conditional, post, func, module);
        case 'while':
            return computeWPWhile(stmt as While, post, func, module);
        default:
            return post;
    }
}

// обработка блоков (упрощённая версия)
function computeWPBlock(block: Block, post: Predicate, func: FunctionDef, module: AnnotatedModule): Predicate {
    let result = post;
    for (let i = block.statements.length - 1; i >= 0; i--) {
        result = computeWP(block.statements[i], result, func, module);
    }
    return result;
}

// обработка присваиваний (упрощённая версия)
function computeWPAssignment(assign: Assignment, post: Predicate, func: FunctionDef, module: AnnotatedModule): Predicate {
    if (assign.value.type === 'call') {
        const call = assign.value as FunctionCall;
        const calledFunc = module.functions.find(f => f.name === call.name);
        if (calledFunc) { 
            let result = post;
            for (let i = assign.targets.length - 1; i >= 0; i--) {
                const target = assign.targets[i];
                const returnVar = calledFunc.returns[i];
                const substitutedExpr: arith.Expr = { type: 'var', name: `${call.name}_ret_${returnVar.name}` };
                result = substitutePredicate(result, target, substitutedExpr);
            }
            let calledEnsures = calledFunc.ensures || { type: 'bool', value: true };
            calledEnsures = substituteCallArgs(calledEnsures, calledFunc, call);
            for (let i = 0; i < calledFunc.returns.length; i++) {
                const returnName = calledFunc.returns[i].name;
                const freshName = `${call.name}_ret_${returnName}`;
                calledEnsures = renameVariable(calledEnsures, returnName, freshName);
            }
            let calledRequires = calledFunc.requires || { type: 'bool', value: true };
            calledRequires = substituteCallArgs(calledRequires, calledFunc, call);
            return {
                type: 'binPred',
                op: 'and',
                left: calledRequires,
                right: { type: 'binPred', op: '->', left: calledEnsures, right: result }
            };
        }
    }
    if (assign.kind === 'simple' && assign.targets.length === 1) {
        return substitutePredicate(post, assign.targets[0], assign.value as arith.Expr);
    }
    if (assign.kind === 'array') {
        return post;
    }
    return post;
}

// подставляет аргументы вызова в предикат вызываемой функции
function substituteCallArgs(pred: Predicate, calledFunc: FunctionDef, call: FunctionCall): Predicate {
    let result = pred;
    for (let i = 0; i < calledFunc.parameters.length && i < call.args.length; i++) {
        result = substitutePredicate(result, calledFunc.parameters[i].name, call.args[i]); // заменяет все вхождения имени параметра на выражение аргумента
    }
    return result;
}

// обрабокта условий (упрощённая версия)
function computeWPConditional(cond: Conditional, post: Predicate, func: FunctionDef, module: AnnotatedModule): Predicate {
    const condPred = conditionToPredicate(cond.condition);
    const wpThen = computeWP(cond.thenBranch, post, func, module);
    if (cond.elseBranch) {
        const wpElse = computeWP(cond.elseBranch, post, func, module);
        return {
            type: 'binPred',
            op: 'and',
            left: { type: 'binPred', op: '->', left: condPred, right: wpThen },
            right: { type: 'binPred', op: '->', left: { type: 'not', argument: condPred }, right: wpElse }
        };
    }
    return {
        type: 'binPred',
        op: 'and',
        left: { type: 'binPred', op: '->', left: condPred, right: wpThen },
        right: { type: 'binPred', op: '->', left: { type: 'not', argument: condPred }, right: post }
    };
}

//собирает все переменные изменяемые в операторе
function getModifiedVariables(stmt: Statement): string[] {
    const vars = new Set<string>(); // множество переменных
    collectModifiedVars(stmt, vars); // запускаем "поиск"
    return Array.from(vars); // преобразуем в массив
}

//рекурсивно собирает изменяемые переменные
function collectModifiedVars(stmt: Statement, vars: Set<string>) {
    switch (stmt.type) {
        case 'block':
            for (const s of (stmt as Block).statements) collectModifiedVars(s, vars);
            break;
        case 'assign':
            for (const t of (stmt as Assignment).targets) vars.add(t);
            break;
        case 'if':
            const c = stmt as Conditional;
            collectModifiedVars(c.thenBranch, vars);
            if (c.elseBranch) collectModifiedVars(c.elseBranch, vars);
            break;
        case 'while':
            collectModifiedVars((stmt as While).body, vars);
            break;
    }
}

// обработка циклов (упрощённая версия)
function computeWPWhile(whileStmt: While, post: Predicate, func: FunctionDef, module: AnnotatedModule): Predicate {
    const inv = whileStmt.invariant || { type: 'bool', value: true };
    const condPred = conditionToPredicate(whileStmt.condition);
    const modifiedVars = getModifiedVariables(whileStmt.body);
    const initCheck: Predicate = inv;
    let preserveCheck: Predicate = {
        type: 'binPred',
        op: '->',
        left: { type: 'binPred', op: 'and', left: inv, right: condPred },
        right: computeWP(whileStmt.body, inv, func, module)
    };
    let exitCheck: Predicate = {
        type: 'binPred',
        op: '->',
        left: { type: 'binPred', op: 'and', left: inv, right: { type: 'not', argument: condPred } },
        right: post
    };
    const isTrivialInv = inv.type === 'bool' && inv.value === true;
    if (!isTrivialInv) {
        for (const varName of modifiedVars) {
            preserveCheck = {
                type: 'quantifier',
                quantifier: 'forall',
                variable: { type: 'param', name: varName, varType: 'int' },
                body: preserveCheck
            };
            exitCheck = {
                type: 'quantifier',
                quantifier: 'forall',
                variable: { type: 'param', name: varName, varType: 'int' },
                body: exitCheck
            };
        }
    }
    return {
        type: 'binPred',
        op: 'and',
        left: initCheck,
        right: { type: 'binPred', op: 'and', left: preserveCheck, right: exitCheck }
    };
}

// преобразует condition из ast в predicate
function conditionToPredicate(cond: any): Predicate {
    switch (cond.type) {
        case 'bool': return { type: 'bool', value: cond.value };
        case 'comp': return { type: 'comp', op: cond.op, left: cond.left, right: cond.right };
        case 'not': return { type: 'not', argument: conditionToPredicate(cond.argument) };
        case 'binCond': return {
            type: 'binPred',
            op: cond.op,
            left: conditionToPredicate(cond.left),
            right: conditionToPredicate(cond.right)
        };
        default: return { type: 'bool', value: true };
    }
}

// заменяет переменную на выражение в предикате
function substitutePredicate(pred: Predicate, varName: string, expr: arith.Expr): Predicate {
    switch (pred.type) {
        case 'bool': return pred;
        case 'comp': return {
            type: 'comp',
            op: pred.op,
            left: substituteExpr(pred.left, varName, expr),
            right: substituteExpr(pred.right, varName, expr)
        };
        case 'not': return { type: 'not', argument: substitutePredicate(pred.argument, varName, expr) };
        case 'binPred': return {
            type: 'binPred',
            op: pred.op,
            left: substitutePredicate(pred.left, varName, expr),
            right: substitutePredicate(pred.right, varName, expr)
        };
        case 'quantifier':
            // не подставляем в связанную переменную
            if (pred.variable.name === varName) return pred;
            return {
                type: 'quantifier',
                quantifier: pred.quantifier,
                variable: pred.variable,
                body: substitutePredicate(pred.body, varName, expr) // если переменная квантора отличается от varName, подстановка применяется к телу квантора
            };
        case 'formulaRef': return {
            type: 'formulaRef',
            name: pred.name,
            args: pred.args.map(arg => substituteExpr(arg, varName, expr))
        };
        default: return pred;
    }
}

// заменяет переменную на выражение в арифметическом выражении
function substituteExpr(e: arith.Expr | any, varName: string, replacement: arith.Expr): arith.Expr {
    switch (e.type) {
        case 'num': return e;
        case 'var': return e.name === varName ? replacement : e;
        case 'binary': return {
            type: 'binary',
            op: e.op,
            left: substituteExpr(e.left, varName, replacement),
            right: substituteExpr(e.right, varName, replacement)
        };
        case 'neg': return { type: 'neg', argument: substituteExpr(e.argument, varName, replacement) };
        case 'call': return {
            type: 'call',
            name: e.name,
            args: e.args.map((arg: any) => substituteExpr(arg, varName, replacement))
        } as any;
        case 'arrayAccess': return {
            type: 'arrayAccess',
            name: e.name,
            index: substituteExpr(e.index, varName, replacement)
        } as any;
        default: return e;
    }
}

// переименовывает переменную в предикате
function renameVariable(pred: Predicate, oldName: string, newName: string): Predicate {
    return substitutePredicate(pred, oldName, { type: 'var', name: newName });
}

// проверяет можно ли преобразовать предикат в wasm код для runtime проверки
function canConvertToWasm(pred: Predicate): boolean {
    switch (pred.type) {
        case 'bool': return true;
        case 'comp': return canConvertExprToWasm(pred.left) && canConvertExprToWasm(pred.right);
        case 'not': return canConvertToWasm(pred.argument);
        case 'binPred': 
            if (pred.op === '->') {
                // импликация a -> b преобразуется в if(a) then b else true
                return canConvertToWasm(pred.left) && canConvertToWasm(pred.right);
            }
            return canConvertToWasm(pred.left) && canConvertToWasm(pred.right);
        case 'quantifier': return false; // кванторы нельзя проверить в runtime
        case 'formulaRef': return false; // ссылки на формулы требуют раскрытия
        default: return false;
    }
}

// проверяет можно ли преобразовать выражение в wasm
function canConvertExprToWasm(expr: arith.Expr | any): boolean {
    switch (expr.type) {
        case 'num': return true;
        case 'var': return true;
        case 'binary': return canConvertExprToWasm(expr.left) && canConvertExprToWasm(expr.right);
        case 'neg': return canConvertExprToWasm(expr.argument);
        case 'arrayAccess': return canConvertExprToWasm(expr.index);
        case 'call': 
            // вызовы функций можно проверить если все аргументы можно
            return expr.args.every((arg: any) => canConvertExprToWasm(arg));
        default: return false;
    }
}

// добавляет runtime проверку для недоказуемого условия
function addRuntimeCheck(vc: VerificationCondition, func: FunctionDef): void {
    runtimeChecks.push({
        condition: vc.predicate, // исходный предикат
        errorMessage: `Runtime verification failed: ${conditionTypeToString(vc.conditionType)}${vc.details ? ` - ${vc.details}` : ''}`, // сообщение об ошибке
        conditionType: vc.conditionType
    });
}

// преобразует тип условия в читаемую строку
function conditionTypeToString(type: ConditionType): string {
    switch (type) {
        case 'precondition': return 'Precondition violated';
        case 'postcondition': return 'Postcondition violated';
        case 'loop_invariant_init': return 'Loop invariant not established';
        case 'loop_invariant_preserve': return 'Loop invariant not preserved';
        case 'loop_invariant_exit': return 'Loop invariant does not imply postcondition';
        case 'function_call_requires': return 'Function call precondition violated';
        case 'array_bounds': return 'Array bounds check failed';
    }
}

// доказывает условие верификации 
async function proveTheoremDetailed(vc: VerificationCondition, func: FunctionDef, module: AnnotatedModule): Promise<VerificationResult> {
    z3Functions.clear();
    const solver = new z3.Solver();
    solver.set('timeout', 10000);
    const vars = new Map<string, any>();
    const arrays = new Map<string, any>();
    collectVariables(vc.predicate, vars, arrays, func); // рекурсивно обходит предикат и собирает все упомянутые переменные
    // добавляем аксиомы функций и массивов
    addFunctionAxioms(solver, module, vars, arrays);
    addArrayAxioms(solver, arrays, vars);
    // добавляем отрицание условия: если unsat то условие истинно
    const negatedVC: Predicate = { type: 'not', argument: vc.predicate };
    const z3vc = convertConditionsToZ3(negatedVC, vars, arrays, func, module);
    solver.add(z3vc);
    const result = await solver.check();
    if (result === 'unsat') {
        // отрицание неудовлетворимо -> условие истинно
        return { valid: true };
    } else if (result === 'sat') {
        // найден контрпример
        const model = solver.model();
        let counterexample: string | undefined;
        try {
            counterexample = printFuncCall(func, model);
        } catch {
            counterexample = undefined;
        }
        return { 
            valid: false, 
            message: `Counterexample found: ${vc.details || conditionTypeToString(vc.conditionType)}`,
            conditionType: vc.conditionType,
            condition: vc.predicate,
            location: {
                funcName: func.name,
                statementType: vc.conditionType,
                details: vc.details
            },
            counterexample 
        };
    } else {
        // unknown - пытаемся использовать runtime верификацию
        if (canConvertToWasm(vc.predicate)) {
            // добавляем runtime проверку
            addRuntimeCheck(vc, func);
            // считаем успехом - проверка будет в runtime
            return { valid: true };
        } else {
            // нельзя преобразовать в wasm - ошибка верификации
            return { 
                valid: false, 
                message: `Cannot prove or disprove and cannot verify at runtime: ${vc.details || conditionTypeToString(vc.conditionType)}`,
                conditionType: vc.conditionType,
                condition: vc.predicate,
                location: {
                    funcName: func.name,
                    statementType: vc.conditionType,
                    details: vc.details
                }
            };
        }
    }
}

//добавляет аксиомы для массивов (длина >= 0)
function addArrayAxioms(solver: any, arrays: Map<string, any>, vars: Map<string, any>): void {
    for (const [name, array] of arrays) {
        const lenVarName = `length_${name}`;
        let lenVar = vars.get(lenVarName);
        if (!lenVar) {
            lenVar = z3.Int.const(lenVarName);
            vars.set(lenVarName, lenVar);
        }
        solver.add(lenVar.ge(0));
    }
}

// упрощённая версия доказательства теоремы
async function proveTheorem(vc: Predicate, func: FunctionDef, module: AnnotatedModule): Promise<{
    valid: boolean;
    message?: string;
    location?: string;
    counterexample?: string;
}> {
    z3Functions.clear();
    const solver = new z3.Solver();
    solver.set('timeout', 10000);
    const vars = new Map<string, any>();
    const arrays = new Map<string, any>();
    collectVariables(vc, vars, arrays, func);
    addFunctionAxioms(solver, module, vars, arrays);
    const negatedVC: Predicate = { type: 'not', argument: vc };
    const z3vc = convertConditionsToZ3(negatedVC, vars, arrays, func, module);
    solver.add(z3vc);
    const result = await solver.check();
    if (result === 'unsat') {
        return { valid: true };
    } else if (result === 'sat') {
        const model = solver.model();
        try {
            const counterexample = printFuncCall(func, model);
            return { 
                valid: false, 
                message: 'Counterexample found',
                location: 'ensures clause',
                counterexample 
            };
        } catch {
            return { valid: false, message: 'Verification failed', location: 'ensures clause' };
        }
    } else {
        return { 
            valid: false, 
            message: 'Cannot prove or disprove (Z3 returned unknown)',
            location: 'verification condition'
        };
    }
}

// извлекает выражение для возвращаемого значения из ensures
function extractEnsuresExpression(ensures: Predicate, returnVarName: string): arith.Expr | null {
    if (ensures.type === 'comp' && ensures.op === '==') {
        if (ensures.left.type === 'var' && ensures.left.name === returnVarName) {
            return ensures.right;
        }
        if (ensures.right.type === 'var' && ensures.right.name === returnVarName) {
            return ensures.left;
        }
    }
    return null;
}

// извлекает условные аксиомы из сложных ensures (для условных выражений)
function extractConditionalAxioms(ensures: Predicate, returnVarName: string): Array<{condition: Predicate | null, expr: arith.Expr}> {
    const axioms: Array<{condition: Predicate | null, expr: arith.Expr}> = []; // cоздает пустой массив для хранения извлеченных аксиом
    const simpleExpr = extractEnsuresExpression(ensures, returnVarName); // ищет паттерны: result == expr или expr == result
    if (simpleExpr) {
        axioms.push({condition: null, expr: simpleExpr});
        return axioms;
    }
    // для or разбираем обе ветки
    if (ensures.type === 'binPred' && ensures.op === 'or') {
        extractFromBranch(ensures.left, returnVarName, axioms);
        extractFromBranch(ensures.right, returnVarName, axioms);
    }
    return axioms;
}

// извлекает аксиому из ветки условного ensures
function extractFromBranch(pred: Predicate, returnVarName: string, axioms: Array<{condition: Predicate | null, expr: arith.Expr}>) {
    const simpleExpr = extractEnsuresExpression(pred, returnVarName); // ищет паттерны: result == expr или expr == result
    if (simpleExpr) {
        axioms.push({condition: null, expr: simpleExpr});
        return;
    }
    // для and ищем условие и выражение
    if (pred.type === 'binPred' && pred.op === 'and') {
        const leftExpr = extractEnsuresExpression(pred.left, returnVarName);
        if (leftExpr) {
            axioms.push({condition: pred.right, expr: leftExpr});
            return;
        }
        const rightExpr = extractEnsuresExpression(pred.right, returnVarName);
        if (rightExpr) {
            axioms.push({condition: pred.left, expr: rightExpr});
            return;
        }
    }
}

// добавляет аксиомы для функций чтобы z3 мог использовать их спецификации
function addFunctionAxioms(solver: any, module: AnnotatedModule, vars: Map<string, any>, arrays: Map<string, any>) {
    for (const func of module.functions) {
        if (!func.ensures) continue; // пропускаем функции без постусловий
        if (func.returns.length !== 1) continue; // пропускаем функции без или с несколькими возвратами
        if (func.parameters.length === 0) continue; // пропускаем функции без параметров
        const returnVarName = func.returns[0].name; // извлекает имя переменной возвращаемого значения
        const conditionalAxioms = extractConditionalAxioms(func.ensures, returnVarName); // извлечение условных аксиом 
        if (conditionalAxioms.length === 0) continue;
        // создаём z3 функцию с нужной сигнатурой
        const argSorts = func.parameters.map(() => z3.Int.sort());
        const z3Func = z3.Function.declare(`fn_${func.name}`, ...argSorts, z3.Int.sort());
        z3Functions.set(func.name, { isConst: false, val: z3Func });
        // создаём переменные для параметров
        const paramVars: any[] = [];
        const paramVarsMap = new Map<string, any>();
        for (const p of func.parameters) {
            const pVar = z3.Int.const(`ax_${func.name}_${p.name}`);
            paramVars.push(pVar);
            paramVarsMap.set(p.name, pVar);
        }
        const funcCall = z3Func.call(...paramVars);
        // добавляем аксиомы: forall args: f(args) == expr
        for (const {condition, expr} of conditionalAxioms) {
            const exprZ3 = convertExprToZ3WithParams(expr, paramVarsMap, arrays, module);
            if (condition) {
                const condZ3 = convertConditionToZ3WithParams(condition, paramVarsMap, arrays, func, module);
                const axiom = z3.ForAll(paramVars as [any, ...any[]], z3.Implies(condZ3, funcCall.eq(exprZ3)));
                solver.add(axiom);
            } else {
                const axiom = z3.ForAll(paramVars as [any, ...any[]], funcCall.eq(exprZ3));
                solver.add(axiom);
            }
        }
    }
}

// преобразует условие в z3 с подстановкой параметров
function convertConditionToZ3WithParams(pred: Predicate, paramVars: Map<string, any>, arrays: Map<string, any>, func: FunctionDef, module: AnnotatedModule): Bool<"main"> {
    switch (pred.type) {
        case 'bool': return pred.value ? z3.Bool.val(true) : z3.Bool.val(false);
        case 'comp': {
            const left = convertExprToZ3WithParams(pred.left, paramVars, arrays, module);
            const right = convertExprToZ3WithParams(pred.right, paramVars, arrays, module);
            switch (pred.op) {
                case '==': return left.eq(right);
                case '!=': return left.neq(right);
                case '<': return left.lt(right);
                case '<=': return left.le(right);
                case '>': return left.gt(right);
                case '>=': return left.ge(right);
            }
        }
        case 'not': return z3.Not(convertConditionToZ3WithParams(pred.argument, paramVars, arrays, func, module));
        case 'binPred': {
            const left = convertConditionToZ3WithParams(pred.left, paramVars, arrays, func, module);
            const right = convertConditionToZ3WithParams(pred.right, paramVars, arrays, func, module);
            switch (pred.op) {
                case 'and': return z3.And(left, right);
                case 'or': return z3.Or(left, right);
                case '->': return z3.Implies(left, right);
            }
        }
        default: return z3.Bool.val(true);
    }
}

// преобразует выражение в z3 с подстановкой параметров
function convertExprToZ3WithParams(expr: arith.Expr | any, paramVars: Map<string, any>, arrays: Map<string, any>, module?: AnnotatedModule): Arith<"main"> {
    switch (expr.type) {
        case 'num': return z3.Int.val(expr.value);
        case 'var': {
            // сначала ищем в параметрах
            const v = paramVars.get(expr.name);
            if (v) return v;
            return z3.Int.const(expr.name);
        }
        case 'binary': {
            const left = convertExprToZ3WithParams(expr.left, paramVars, arrays, module);
            const right = convertExprToZ3WithParams(expr.right, paramVars, arrays, module);
            switch (expr.op) {
                case '+': return left.add(right);
                case '-': return left.sub(right);
                case '*': return left.mul(right);
                case '/': return z3.Int.val(0).add(left).div(right);
            }
        }
        case 'neg': {
            const arg = convertExprToZ3WithParams(expr.argument, paramVars, arrays, module);
            return z3.Int.val(0).sub(arg);
        }
        case 'call': {
            let z3FuncEntry = z3Functions.get(expr.name);
            if (!z3FuncEntry) {
                if (expr.args.length === 0) {
                    const z3Const = z3.Int.const(`func_${expr.name}`);
                    z3Functions.set(expr.name, { isConst: true, val: z3Const });
                    return z3Const;
                }
                const argSorts = expr.args.map(() => z3.Int.sort());
                const z3Func = z3.Function.declare(`fn_${expr.name}`, ...argSorts, z3.Int.sort());
                z3Functions.set(expr.name, { isConst: false, val: z3Func });
                const z3Args = expr.args.map((arg: any) => convertExprToZ3WithParams(arg, paramVars, arrays, module));
                return z3Func.call(...z3Args);
            } else if (z3FuncEntry.isConst) {
                return z3FuncEntry.val;
            } else {
                const z3Args = expr.args.map((arg: any) => convertExprToZ3WithParams(arg, paramVars, arrays, module));
                return z3FuncEntry.val.call(...z3Args);
            }
        }
        default: return z3.Int.val(0);
    }
}

// собирает все переменные из функции и предиката
function collectVariables(pred: Predicate, vars: Map<string, any>, arrays: Map<string, any>, func: FunctionDef) {
    //добавляем параметры функции
    for (const p of func.parameters) {
        if (p.varType === 'int') {
            if (!vars.has(p.name)) vars.set(p.name, z3.Int.const(p.name));
        } else {
            if (!arrays.has(p.name)) arrays.set(p.name, z3.Array.const(p.name, z3.Int.sort(), z3.Int.sort()));
        }
    }
    // добавляем возвращаемые переменные
    for (const r of func.returns) {
        if (r.varType === 'int') {
            if (!vars.has(r.name)) vars.set(r.name, z3.Int.const(r.name));
        } else {
            if (!arrays.has(r.name)) arrays.set(r.name, z3.Array.const(r.name, z3.Int.sort(), z3.Int.sort()));
        }
    }
    // добавляем локальные переменные
    for (const l of func.locals) {
        if (l.varType === 'int') {
            if (!vars.has(l.name)) vars.set(l.name, z3.Int.const(l.name));
        } else {
            if (!arrays.has(l.name)) arrays.set(l.name, z3.Array.const(l.name, z3.Int.sort(), z3.Int.sort()));
        }
    }
    // добавляем переменные из предиката
    collectVariablesFromPredicate(pred, vars, arrays);
}

// рекурсивно собирает переменные из предиката
function collectVariablesFromPredicate(pred: Predicate, vars: Map<string, any>, arrays: Map<string, any>) {
    switch (pred.type) {
        case 'comp':
            collectVariablesFromExpr(pred.left, vars, arrays);
            collectVariablesFromExpr(pred.right, vars, arrays);
            break;
        case 'not':
            collectVariablesFromPredicate(pred.argument, vars, arrays);
            break;
        case 'binPred':
            collectVariablesFromPredicate(pred.left, vars, arrays);
            collectVariablesFromPredicate(pred.right, vars, arrays);
            break;
        case 'quantifier':
            //добавляем связанную переменную
            if (!vars.has(pred.variable.name)) {
                vars.set(pred.variable.name, z3.Int.const(pred.variable.name));
            }
            collectVariablesFromPredicate(pred.body, vars, arrays);
            break;
        case 'formulaRef':
            for (const arg of pred.args) {
                collectVariablesFromExpr(arg, vars, arrays);
            }
            break;
    }
}

// рекурсивно собирает переменные из выражения
function collectVariablesFromExpr(expr: arith.Expr | any, vars: Map<string, any>, arrays: Map<string, any>) {
    switch (expr.type) {
        case 'var':
            if (!vars.has(expr.name)) vars.set(expr.name, z3.Int.const(expr.name));
            break;
        case 'binary':
            collectVariablesFromExpr(expr.left, vars, arrays);
            collectVariablesFromExpr(expr.right, vars, arrays);
            break;
        case 'neg':
            collectVariablesFromExpr(expr.argument, vars, arrays);
            break;
        case 'arrayAccess':
            if (!arrays.has(expr.name)) {
                arrays.set(expr.name, z3.Array.const(expr.name, z3.Int.sort(), z3.Int.sort()));
            }
            collectVariablesFromExpr(expr.index, vars, arrays);
            break;
        case 'call':
            for (const arg of expr.args) {
                collectVariablesFromExpr(arg, vars, arrays);
            }
            break;
    }
}

// преобразует предикат funny в z3 формулу
function convertConditionsToZ3(pred: Predicate, vars: Map<string, any>, arrays: Map<string, any>, func: FunctionDef, module: AnnotatedModule): Bool<"main"> {
    switch (pred.type) {
        case 'bool': return pred.value ? z3.Bool.val(true) : z3.Bool.val(false);
        case 'comp': {
            //сравнение: преобразуем левое и правое выражение
            const left = convertExprToZ3(pred.left, vars, arrays, module);
            const right = convertExprToZ3(pred.right, vars, arrays, module);
            switch (pred.op) {
                case '==': return left.eq(right);
                case '!=': return left.neq(right);
                case '<': return left.lt(right);
                case '<=': return left.le(right);
                case '>': return left.gt(right);
                case '>=': return left.ge(right);
            }
        }
        case 'not': return z3.Not(convertConditionsToZ3(pred.argument, vars, arrays, func, module));
        case 'binPred': {
            const left = convertConditionsToZ3(pred.left, vars, arrays, func, module);
            const right = convertConditionsToZ3(pred.right, vars, arrays, func, module);
            switch (pred.op) {
                case 'and': return z3.And(left, right);
                case 'or': return z3.Or(left, right);
                case '->': return z3.Implies(left, right);
            }
        }
        case 'quantifier': {
            //кванторы: создаём связанную переменную и оборачиваем
            const qVar = z3.Int.const(pred.variable.name);
            vars.set(pred.variable.name, qVar);
            const body = convertConditionsToZ3(pred.body, vars, arrays, func, module);
            if (pred.quantifier === 'forall') {
                return z3.ForAll([qVar], body);
            } else {
                return z3.Exists([qVar], body);
            }
        }
        case 'formulaRef': {
            //ссылка на формулу: преобразуем в вызов z3 функции
            let z3FuncEntry = z3Functions.get(pred.name);
            let result: any;
            if (!z3FuncEntry) {
                if (pred.args.length === 0) {
                    //функция без аргументов - константа
                    result = z3.Int.const(`func_${pred.name}`);
                    z3Functions.set(pred.name, { isConst: true, val: result });
                } else {
                    //функция с аргументами
                    const argSorts = pred.args.map(() => z3.Int.sort());
                    const z3Func = z3.Function.declare(`fn_${pred.name}`, ...argSorts, z3.Int.sort());
                    z3Functions.set(pred.name, { isConst: false, val: z3Func });
                    const z3Args = pred.args.map((arg: any) => convertExprToZ3(arg, vars, arrays, module));
                    result = z3Func.call(...z3Args);
                }
            } else if (z3FuncEntry.isConst) {
                result = z3FuncEntry.val;
            } else {
                const z3Args = pred.args.map((arg: any) => convertExprToZ3(arg, vars, arrays, module));
                result = z3FuncEntry.val.call(...z3Args);
            }
            //formulaRef возвращает bool: result != 0
            return result.neq(z3.Int.val(0));
        }
        default: return z3.Bool.val(true);
    }
}

// преобразует выражение funny в z3 арифметику
function convertExprToZ3(expr: arith.Expr | any, vars: Map<string, any>, arrays: Map<string, any>, module?: AnnotatedModule): Arith<"main"> {
    switch (expr.type) {
        case 'num': return z3.Int.val(expr.value);
        case 'var': {
            //ищем переменную или создаём новую
            let v = vars.get(expr.name);
            if (!v) {
                v = z3.Int.const(expr.name);
                vars.set(expr.name, v);
            }
            return v;
        }
        case 'binary': {
            const left = convertExprToZ3(expr.left, vars, arrays, module);
            const right = convertExprToZ3(expr.right, vars, arrays, module);
            switch (expr.op) {
                case '+': return left.add(right);
                case '-': return left.sub(right);
                case '*': return left.mul(right);
                case '/': return z3.Int.val(0).add(left).div(right);
            }
        }
        case 'neg': {
            const arg = convertExprToZ3(expr.argument, vars, arrays, module);
            return z3.Int.val(0).sub(arg);
        }
        case 'arrayAccess': {
            //доступ к массиву: arr.select(index)
            let arr = arrays.get(expr.name);
            if (!arr) {
                arr = z3.Array.const(expr.name, z3.Int.sort(), z3.Int.sort());
                arrays.set(expr.name, arr);
            }
            const idx = convertExprToZ3(expr.index, vars, arrays, module);
            return arr.select(idx) as unknown as Arith<"main">;
        }
        case 'call': {
            //специальная обработка length()
            if (expr.name === 'length' && expr.args.length === 1) {
                const arrArg = expr.args[0];
                const lenVarName = `length_${arrArg.name || 'arr'}`;
                let lenVar = vars.get(lenVarName);
                if (!lenVar) {
                    lenVar = z3.Int.const(lenVarName);
                    vars.set(lenVarName, lenVar);
                }
                return lenVar;
            }
            //обычный вызов функции: ищем или создаём z3 функцию
            let z3FuncEntry = z3Functions.get(expr.name);
            if (!z3FuncEntry) {
                if (expr.args.length === 0) {
                    //функция без аргументов - константа
                    const z3Const = z3.Int.const(`func_${expr.name}`);
                    z3Functions.set(expr.name, { isConst: true, val: z3Const });
                    return z3Const;
                }
                //создаём новую z3 функцию
                const argSorts = expr.args.map(() => z3.Int.sort());
                const z3Func = z3.Function.declare(`fn_${expr.name}`, ...argSorts, z3.Int.sort());
                z3Functions.set(expr.name, { isConst: false, val: z3Func });
                const z3Args = expr.args.map((arg: any) => convertExprToZ3(arg, vars, arrays, module));
                return z3Func.call(...z3Args);
            } else if (z3FuncEntry.isConst) {
                return z3FuncEntry.val;
            } else {
                //используем существующую функцию
                const z3Args = expr.args.map((arg: any) => convertExprToZ3(arg, vars, arrays, module));
                return z3FuncEntry.val.call(...z3Args);
            }
        }
        default: return z3.Int.val(0);
    }
}
