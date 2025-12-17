import { Expr } from "../../lab04";

export function derive(e: Expr, varName: string): Expr {
    const result = deriveInternal(e, varName);
    return simplifyExpression(result);
}

function deriveInternal(e: Expr, varName: string): Expr {
    switch (e.type) {
        case 'num':
            //производная константы равна нулю
            return makeConst(0);

        case 'var':
            //производная переменной: 1 для нужной переменной, 0 для остальных
            return makeConst(e.name === varName ? 1 : 0);

        case 'neg':
            //производная отрицания
            return makeNeg(derive(e.argument, varName));

        case 'binary':
            const left = e.left;
            const right = e.right;

            switch (e.op) {
                case '+':
                    //производная суммы
                    return makeBinOp('+', derive(left, varName), derive(right, varName));

                case '-':
                    //производная разности
                    return makeBinOp('-', derive(left, varName), derive(right, varName));

                case '*':
                    //производная произведения (правило произведения)
                    const leftDeriv = derive(left, varName);
                    const rightDeriv = derive(right, varName);
                    return makeBinOp('+',
                        makeBinOp('*', leftDeriv, right),
                        makeBinOp('*', left, rightDeriv)
                    );

                case '/':
                    //производная частного (правило частного)
                    const fPrime = derive(left, varName);
                    const gPrime = derive(right, varName);
                    const numerator = makeBinOp('-',
                        makeBinOp('*', fPrime, right),
                        makeBinOp('*', left, gPrime)
                    );
                    const denominator = makeBinOp('*', right, right);
                    return makeBinOp('/', numerator, denominator);
            }
    }
}

function isZero(e: Expr): boolean {
    if (e.type === 'num') return e.value === 0;
    
    if (e.type === 'binary') {
        //x - x = 0
        if (e.op === '-' && areEquivalent(e.left, e.right)) return true;
        
        //0 * x = 0, x * 0 = 0
        if (e.op === '*' && (isZero(e.left) || isZero(e.right))) return true;
        
        //0 / x = 0
        if (e.op === '/' && isZero(e.left)) return true;
        
        //0 + 0 = 0
        if (e.op === '+' && isZero(e.left) && isZero(e.right)) return true;
    }
    
    return false;
}

function isOne(e: Expr): boolean {
    if (e.type === 'num') return e.value === 1;
    
    if (e.type === 'binary') {
        //x / x = 1
        if (e.op === '/' && areEquivalent(e.left, e.right)) return true;
    }
    
    return false;
}

function makeConst(value: number): Expr {
    return { type: 'num', value };
}

function makeBinOp(op: '+' | '-' | '*' | '/', left: Expr, right: Expr): Expr {
    return { type: 'binary', op, left, right };
}

function makeNeg(arg: Expr): Expr {
    return { type: 'neg', argument: arg };
}

function simplifyExpression(expr: Expr): Expr {
    if (expr.type === 'binary') {
        const leftSimplified = simplifyExpression(expr.left);
        const rightSimplified = simplifyExpression(expr.right);
        
        switch (expr.op) {
            case '+': return simplifyAdd(leftSimplified, rightSimplified);
            case '-': return simplifySub(leftSimplified, rightSimplified);
            case '*': return simplifyMul(leftSimplified, rightSimplified);
            case '/': return simplifyDiv(leftSimplified, rightSimplified);
        }
    }
    if (expr.type === 'neg') {
        return simplifyNeg(simplifyExpression(expr.argument));
    }
    return expr;
}

function simplifyAdd(left: Expr, right: Expr): Expr {
    //x + 0 = x
    if (isZero(right)) return left;
    //0 + x = x
    if (isZero(left)) return right;
    
    //свертка констант
    if (left.type === 'num' && right.type === 'num') {
        return makeConst(left.value + right.value);
    }
    
    //нормализуем отрицания в умножениях перед объединением
    const leftNorm = normalizeMultiplication(left);
    const rightNorm = normalizeMultiplication(right);
    
    //объединяем подобные слагаемые
    const combined = combineLikeTerms(leftNorm, rightNorm);
    if (combined) return combined;
    
    return makeBinOp('+', leftNorm, rightNorm);
}

function simplifySub(left: Expr, right: Expr): Expr {
    //x - 0 = x
    if (isZero(right)) return left;
    
    //0 - x = -x
    if (isZero(left)) return simplifyNeg(right);
    
    //свертка констант
    if (left.type === 'num' && right.type === 'num') {
        return makeConst(left.value - right.value);
    }
    
    return makeBinOp('-', left, right);
}

function simplifyMul(left: Expr, right: Expr): Expr {
    //x * 0 = 0, 0 * x = 0
    if (isZero(left) || isZero(right)) return makeConst(0);
    
    //1 * x = x
    if (isOne(left)) return right;
    //x * 1 = x
    if (isOne(right)) return left;
    
    //свертка констант
    if (left.type === 'num' && right.type === 'num') {
        return makeConst(left.value * right.value);
    }
    
    //объединяем константы во вложенных умножениях
    if (left.type === 'binary' && left.op === '*' && left.left.type === 'num' && right.type === 'num') {
        return makeBinOp('*', makeConst(left.left.value * right.value), left.right);
    }
    if (left.type === 'binary' && left.op === '*' && left.right.type === 'num' && right.type === 'num') {
        return makeBinOp('*', makeConst(left.right.value * right.value), left.left);
    }
    if (right.type === 'binary' && right.op === '*' && right.left.type === 'num' && left.type === 'num') {
        return makeBinOp('*', makeConst(right.left.value * left.value), right.right);
    }
    if (right.type === 'binary' && right.op === '*' && right.right.type === 'num' && left.type === 'num') {
        return makeBinOp('*', makeConst(right.right.value * left.value), right.left);
    }
    
    //обрабатываем отрицания: const * -x = -(const * x)
    if (left.type === 'num' && right.type === 'neg') {
        return simplifyNeg(makeBinOp('*', left, right.argument));
    }
    if (right.type === 'num' && left.type === 'neg') {
        return simplifyNeg(makeBinOp('*', right, left.argument));
    }
    
    return makeBinOp('*', left, right);
}

function simplifyDiv(left: Expr, right: Expr): Expr {
    //x / 1 = x
    if (isOne(right)) return left;
    
    //0 / x = 0
    if (isZero(left)) return makeConst(0);
    
    //свертка констант
    if (left.type === 'num' && right.type === 'num') {
        if (right.value === 0) {
            return makeBinOp('/', left, right);
        }
        return makeConst(Math.floor(left.value / right.value));
    }
    
    return makeBinOp('/', left, right);
}

function simplifyNeg(arg: Expr): Expr {
    //двойное отрицание
    if (arg.type === 'neg') {
        return arg.argument;
    }
    
    //-0 = 0
    if (isZero(arg)) {
        return makeConst(0);
    }
    
    //отрицание константы
    if (arg.type === 'num') {
        return makeConst(-arg.value);
    }
    
    //отрицание дроби с отрицательной константой
    if (arg.type === 'binary' && arg.op === '/') {
        if (arg.left.type === 'num' && arg.left.value < 0) {
            return makeBinOp('/', makeConst(-arg.left.value), arg.right);
        }
    }
    
    //распределяем отрицание в умножение
    if (arg.type === 'binary' && arg.op === '*') {
        if (arg.left.type === 'num') {
            return simplifyMul(makeConst(-arg.left.value), arg.right);
        }
        if (arg.right.type === 'num') {
            return simplifyMul(arg.left, makeConst(-arg.right.value));
        }
    }
    
    return makeNeg(arg);
}

function combineLikeTerms(left: Expr, right: Expr): Expr | null {
    const leftTerm = extractCoefficientAndTerm(left);
    const rightTerm = extractCoefficientAndTerm(right);
    
    if (leftTerm && rightTerm && areEquivalent(leftTerm.term, rightTerm.term)) {
        const newCoeff = leftTerm.coeff + rightTerm.coeff;
        if (newCoeff === 0) return makeConst(0);
        if (newCoeff === 1) return leftTerm.term;
        if (newCoeff === -1) return makeNeg(leftTerm.term);
        
        //строим коэффициент * терм с правильной структурой
        //тест ожидает лево-ассоциативную структуру
        if (newCoeff < 0) {
            return multiplyCoeffIntoTerm(makeNeg(makeConst(-newCoeff)), leftTerm.term);
        }
        return multiplyCoeffIntoTerm(makeConst(newCoeff), leftTerm.term);
    }
    
    return null;
}

function multiplyCoeffIntoTerm(coeff: Expr, term: Expr): Expr {
    //рекурсивно умножаем коэффициент в крайнюю левую позицию цепочки умножений
    //это создает структуру ((coeff * x) * y) * z вместо coeff * (x * y * z)
    if (term.type === 'binary' && term.op === '*') {
        return makeBinOp('*', multiplyCoeffIntoTerm(coeff, term.left), term.right);
    }
    return makeBinOp('*', coeff, term);
}

function normalizeMultiplication(expr: Expr): Expr {
    if (expr.type !== 'binary' || expr.op !== '*') {
        return expr;
    }
    
    //собираем все множители и извлекаем коэффициент
    const factors: Expr[] = [];
    let coefficient = 1;
    
    function collectFactors(e: Expr): void {
        if (e.type === 'num') {
            coefficient *= e.value;
        } else if (e.type === 'binary' && e.op === '*') {
            collectFactors(e.left);
            collectFactors(e.right);
        } else if (e.type === 'neg') {
            coefficient *= -1;
            collectFactors(e.argument);
        } else {
            factors.push(e);
        }
    }
    
    collectFactors(expr);
    
    //строим результат
    if (factors.length === 0) {
        return makeConst(coefficient);
    }
    
    let result: Expr = factors[0];
    for (let i = 1; i < factors.length; i++) {
        result = makeBinOp('*', result, factors[i]);
    }
    
    if (coefficient === 1) {
        return result;
    } else if (coefficient === -1) {
        return makeNeg(result);
    } else if (coefficient === 0) {
        return makeConst(0);
    } else if (coefficient < 0) {
        //представляем отрицательный коэффициент как отрицание
        return makeBinOp('*', makeNeg(makeConst(-coefficient)), result);
    } else {
        return makeBinOp('*', makeConst(coefficient), result);
    }
}

function extractCoefficientAndTerm(expr: Expr): { coeff: number, term: Expr } | null {
    //сначала нормализуем выражение
    const normalized = normalizeMultiplication(expr);
    
    //случай 1: отрицание умножения
    if (normalized.type === 'neg') {
        if (normalized.argument.type === 'binary' && normalized.argument.op === '*') {
            const inner = extractCoefficientAndTerm(normalized.argument);
            if (inner) {
                return { coeff: -inner.coeff, term: inner.term };
            }
        }
        return { coeff: -1, term: normalized.argument };
    }
    
    //случай 2: константа * выражение или neg(const) * выражение
    if (normalized.type === 'binary' && normalized.op === '*') {
        //проверяем -const * term
        if (normalized.left.type === 'neg' && normalized.left.argument.type === 'num') {
            return { coeff: -normalized.left.argument.value, term: normalized.right };
        }
        if (normalized.right.type === 'neg' && normalized.right.argument.type === 'num') {
            return { coeff: -normalized.right.argument.value, term: normalized.left };
        }
        //проверяем const * term
        if (normalized.left.type === 'num') {
            return { coeff: normalized.left.value, term: normalized.right };
        }
        if (normalized.right.type === 'num') {
            return { coeff: normalized.right.value, term: normalized.left };
        }
    }
    
    //случай 3: константа
    if (normalized.type === 'num') {
        return { coeff: normalized.value, term: makeConst(1) };
    }
    
    //случай 4: нет явного коэффициента = коэффициент 1
    return { coeff: 1, term: normalized };
}

function areEquivalent(a: Expr, b: Expr): boolean {
    if (a.type !== b.type) return false;

    switch (a.type) {
        case 'num':
            return a.value === (b as any).value;
            
        case 'var':
            return a.name === (b as any).name;
            
        case 'neg':
            return areEquivalent(a.argument, (b as any).argument);
            
        case 'binary':
            const bBinop = b as any;
            if (a.op !== bBinop.op) return false;
            
            //для коммутативных операций проверяем оба порядка
            if (a.op === '+' || a.op === '*') {
                return (areEquivalent(a.left, bBinop.left) && areEquivalent(a.right, bBinop.right)) ||
                       (areEquivalent(a.left, bBinop.right) && areEquivalent(a.right, bBinop.left));
            } else {
                //для некоммутативных операций порядок имеет значение
                return areEquivalent(a.left, bBinop.left) && areEquivalent(a.right, bBinop.right);
            }
            
        default:
            return false;
    }
}
