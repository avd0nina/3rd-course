import { Expr } from "../../lab04";
import { cost } from "./cost";
import { printExpr } from "../../lab04";

type Bindings = Map<string, Expr>;

// Pattern matching: проверяет, соответствует ли выражение паттерну
function match(pattern: Expr, expr: Expr, bindings: Bindings = new Map()): Bindings | null {
    if (pattern.type === 'var') {
        const existing = bindings.get(pattern.name);
        if (existing) {
            return exprEquals(existing, expr) ? bindings : null;
        }
        const newBindings = new Map(bindings);
        newBindings.set(pattern.name, expr);
        return newBindings;
    }
    if (pattern.type === 'num' && expr.type === 'num') {
        return pattern.value === expr.value ? bindings : null;
    }
    if (pattern.type === 'neg' && expr.type === 'neg') {
        return match(pattern.arg, expr.arg, bindings);
    }
    if (pattern.type === 'bin' && expr.type === 'bin') {
        if (pattern.op !== expr.op) return null;
        const leftMatch = match(pattern.left, expr.left, bindings);
        if (!leftMatch) return null;
        return match(pattern.right, expr.right, leftMatch);
    }
    return null;
}

// Проверка равенства выражений
function exprEquals(e1: Expr, e2: Expr): boolean {
    if (e1.type !== e2.type) return false;
    switch (e1.type) {
        case 'num':
            return e2.type === 'num' && e1.value === e2.value;
        case 'var':
            return e2.type === 'var' && e1.name === e2.name;
        case 'neg':
            return e2.type === 'neg' && exprEquals(e1.arg, e2.arg);
        case 'bin':
            return e2.type === 'bin' && 
                   e1.op === e2.op && 
                   exprEquals(e1.left, e2.left) && 
                   exprEquals(e1.right, e2.right);
    }
}

// Подстановка переменных в паттерне
function substitute(pattern: Expr, bindings: Bindings): Expr {
    switch (pattern.type) {
        case 'var':
            return bindings.get(pattern.name) || pattern;
        case 'num':
            return pattern;
        case 'neg':
            return { type: 'neg', arg: substitute(pattern.arg, bindings) };
        case 'bin':
            return {
                type: 'bin',
                op: pattern.op,
                left: substitute(pattern.left, bindings),
                right: substitute(pattern.right, bindings)
            };
    }
}

// Constant folding - вычисление константных выражений
function evaluate(e: Expr): Expr {
    switch (e.type) {
        case 'num':
        case 'var':
            return e;
        case 'neg': {
            const arg = evaluate(e.arg);
            if (arg.type === 'num') {
                return { type: 'num', value: -arg.value };
            }
            return { type: 'neg', arg: arg };
        }
        case 'bin': {
            const left = evaluate(e.left);
            const right = evaluate(e.right);
            if (left.type === 'num' && right.type === 'num') {
                let result: number;
                switch (e.op) {
                    case '+': result = left.value + right.value; break;
                    case '-': result = left.value - right.value; break;
                    case '*': result = left.value * right.value; break;
                    case '/': result = left.value / right.value; break;
                }
                return { type: 'num', value: result };
            }
            return { type: 'bin', op: e.op, left, right };
        }
    }
}

// Применение одного тождества к выражению
function applyIdentity(expr: Expr, pattern: Expr, replacement: Expr): Expr | null {
    const bindings = match(pattern, expr);
    if (bindings) {
        return substitute(replacement, bindings);
    }
    return null;
}

// Применение всех тождеств только к корню выражения (без рекурсии)
function applyIdentitiesToRoot(expr: Expr, identities: [Expr, Expr][]): Expr[] {
    const results: Expr[] = [];
    // Пробуем применить каждое тождество в обе стороны
    for (const [left, right] of identities) {
        const result1 = applyIdentity(expr, left, right);
        if (result1) results.push(result1);
        const result2 = applyIdentity(expr, right, left);
        if (result2) results.push(result2);
    }
    return results;
}

// Рекурсивное упрощение снизу вверх (одна итерация)
function simplifyBottomUpOnce(expr: Expr, identities: [Expr, Expr][]): Expr {
    // Сначала рекурсивно упрощаем подвыражения
    let current: Expr;
    switch (expr.type) {
        case 'num':
        case 'var':
            current = expr;
            break;
        case 'neg':
            current = { 
                type: 'neg', 
                arg: simplifyBottomUpOnce(expr.arg, identities) 
            };
            break;
        case 'bin':
            current = {
                type: 'bin',
                op: expr.op,
                left: simplifyBottomUpOnce(expr.left, identities),
                right: simplifyBottomUpOnce(expr.right, identities)
            };
            break;
    }
    // Применяем constant folding
    current = evaluate(current);
    // Пробуем применить тождества с помощью мини-BFS
    const queue: Expr[] = [current];
    const visited = new Set<string>();
    visited.add(printExpr(current));
    let best = current;
    let bestCost = cost(current);
    let iterations = 0;
    while (queue.length > 0 && iterations < 2000) {
        const node = queue.shift()!;
        const nodeCost = cost(node);
        if (nodeCost < bestCost) {
            best = node;
            bestCost = nodeCost;
        }
        if (bestCost === 0) break;
        for (const [left, right] of identities) {
            const result1 = applyIdentity(node, left, right);
            if (result1) {
                const evaluated = evaluate(result1);
                const exprStr = printExpr(evaluated);
                if (!visited.has(exprStr)) {
                    visited.add(exprStr);
                    queue.push(evaluated);
                }
            }
            const result2 = applyIdentity(node, right, left);
            if (result2) {
                const evaluated = evaluate(result2);
                const exprStr = printExpr(evaluated);
                if (!visited.has(exprStr)) {
                    visited.add(exprStr);
                    queue.push(evaluated);
                }
            }
        }
        iterations++;
    }
    return best;
}

// Применение тождеств ко всему дереву выражений
function applyIdentitiesRecursively(expr: Expr, identities: [Expr, Expr][]): Expr[] {
    const results: Expr[] = [];
    // Применяем тождества к корню
    const rootResults = applyIdentitiesToRoot(expr, identities);
    results.push(...rootResults);
    // Применяем тождества к непосредственным подвыражениям
    switch (expr.type) {
        case 'neg': {
            const argResults = applyIdentitiesToRoot(expr.arg, identities);
            for (const arg of argResults) {
                results.push({ type: 'neg', arg: arg });
            }
            break;
        }
        case 'bin': {
            const leftResults = applyIdentitiesToRoot(expr.left, identities);
            for (const left of leftResults) {
                results.push({ type: 'bin', op: expr.op, left, right: expr.right });
            }
            const rightResults = applyIdentitiesToRoot(expr.right, identities);
            for (const right of rightResults) {
                results.push({ type: 'bin', op: expr.op, left: expr.left, right });
            }
            break;
        }
    }
    return results;
}

function simplifyOnce(e: Expr, identities: [Expr, Expr][]): Expr {
    // Применяем constant folding к исходному выражению
    let start = evaluate(e);
    // BFS для поиска выражения с минимальной стоимостью
    const queue: Expr[] = [start];
    const visited = new Set<string>();
    visited.add(printExpr(start));
    let best = start;
    let bestCost = cost(start);
    while (queue.length > 0 && visited.size < 5000) {
        const current = queue.shift()!;
        const currentCost = cost(current);
        if (currentCost < bestCost) {
            best = current;
            bestCost = currentCost;
        }
        // Останавливаемся если достигли стоимости 0 
        if (bestCost === 0) break;
        // Получаем все возможные преобразования
        const candidates = applyIdentitiesRecursively(current, identities);
        for (const candidate of candidates) {
            // Применяем constant folding к кандидату
            const evaluated = evaluate(candidate);
            const candidateStr = printExpr(evaluated);
            if (!visited.has(candidateStr)) {
                visited.add(candidateStr);
                queue.push(evaluated);
            }
        }
    }
    return best;
}

export function simplify(e: Expr, identities: [Expr, Expr][]): Expr {
    let result = e;
    let prev: Expr;
    let iterations = 0;
    // Итеративно применяем bottom-up упрощение
    do {
        prev = result;
        result = simplifyBottomUpOnce(result, identities);
        console.log(`${printExpr(e)} => ${printExpr(result)}`); // current candidate
        iterations++;
    } while (!exprEquals(prev, result) && iterations < 15);
    // Если ничего не изменилось или результат не оптимален, пробуем глобальный BFS
    if (exprEquals(result, e) || cost(result) > 1) {
        const bfsResult = simplifyOnce(result, identities);
        console.log(`${printExpr(e)} => ${printExpr(result)}`); // current candidate
        if (cost(bfsResult) < cost(result)) {
            result = bfsResult;
        }
    }
    return result;
}
