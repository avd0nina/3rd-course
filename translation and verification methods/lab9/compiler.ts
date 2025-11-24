import { Op, I32, Void, c, BufferedEmitter, LocalEntry, Uint8, Int, ExportEntry } from "../../wasm";
import { Module, Statement, Assignment, Block, Conditional, While, Condition, BoolLiteral, Comparison, NotCondition, BinaryCondition, FunctionCall, ArrayAccess } from "../../lab08";
import * as arith from "../../lab04"; 

const {
    i32,
    varuint32,
    get_local,
    local_entry,
    set_local,
    call,
    if_,
    void_block,
    void_loop,
    br_if,
    str_ascii,
    export_entry,
    func_type_m,
    function_body,
    type_section,
    function_section,
    export_section,
    code_section
} = c;

export async function compileModule<M extends Module>(m: M, name?: string): Promise<WebAssembly.Exports> {
    const typeSection: any[] = []; // сигнатуры функций (параметры и возвращаемые значения)
    const functionSection: any[] = []; // индексы типов функций 
    const exportSection: ExportEntry[] = []; // экспортирует функции под их исходными именами
    const codeSection: any[] = [];
    const functionIndexMap = new Map<string, number>(); // создает карту "имя функции" -> "индекс" для быстрого поиска

for (let i = 0; i < m.functions.length; i++) {
    const func = m.functions[i];
    functionIndexMap.set(func.name, i);
    const parametersTypes = func.parameters.map(() => i32);
    const returnTypes = func.returns.map(() => i32);
    
    typeSection.push(c.func_type_m(parametersTypes, returnTypes));
    functionSection.push(c.varuint32(i));
    exportSection.push(
        c.export_entry(
            c.str_ascii(func.name), // имя функции
            c.external_kind.function,   // функция
            c.varuint32(i) // номер функции
        )
    );
}

    for (let i = 0; i < m.functions.length; i++) {
        const func = m.functions[i];
        const localVars: string[] = [ // создает единый массив имен всех локальных переменных функции
            ...func.parameters.map(p => p.name), 
            ...func.returns.map(r => r.name),
            ...func.locals.map(l => l.name)
        ];
        const localEntries: LocalEntry[] = [
            c.local_entry(c.varuint32(localVars.length), i32) // создает запись о группе локальных переменных одного типа
        ];
        const bodyOps: (Op<Void> | Op<I32>)[] = compileStatement(func.body, localVars, functionIndexMap); // компилирует тело функции в байткод wasm
        for (const ret of func.returns) { // добавляет инструкции возврата значений
            const idx = localVars.indexOf(ret.name);
            bodyOps.push(c.get_local(i32, idx));
        }
        codeSection.push(c.function_body(localEntries, bodyOps)); // формирует и добавляет тело функции в секцию кода
    }

    const mod = c.module([ // создает корневую структуру wasm модуля
        c.type_section(typeSection),
        c.function_section(functionSection),
        c.export_section(exportSection),
        c.code_section(codeSection)
    ]);
    const emitter = new BufferedEmitter(new ArrayBuffer(mod.z)); // cоздает эмиттер для генерации бинарного wasm файла
    mod.emit(emitter); // генерирует бинарный wasm код в буфер
    const wasmModule = await WebAssembly.instantiate(emitter.buffer); // компилирует wasm модуль
    return wasmModule.instance.exports; // возвращает экспортированные функции
}

// преобразует AST выражение в WASM инструкции
function compileExpr(expr: any, locals: string[], functionIndexMap: Map<string, number>): Op<I32> {
    if (expr.type === "call") 
        return compileFunctionCall(expr, locals, functionIndexMap);

    //     { // вызов функции
    //     const args = expr.args.map((a: any) => compileExpr(a, locals, functionIndexMap)); // pекурсивно компилирует все аргументы функции
    //     const idx = functionIndexMap.get(expr.name);
    //     if (idx === undefined) throw new Error(`Unknown function: ${expr.name}`);
    //     return c.call(i32, c.varuint32(idx), args); // cоздает wasm инструкцию
    // }
    if (expr.type === "arrayAccess") { // доступ к элементам массива
        const base = c.get_local(i32, locals.indexOf(expr.name)); // base содержит инструкцию, которая загрузит адрес начала массива в стек wasm
        const index = compileExpr(expr.index, locals, functionIndexMap); // pекурсивно компилирует выражение индекса
        const addr = i32.add(base, i32.mul(index, i32.const(4))); // вычисляет адрес нужного элемента массива. 
        // i32.const(4) - создает константу 4 (размер элемента массива в байтах)
        // i32.mul(index, i32.const(4)) - умножает индекс на размер элемента - получает смещение в байтах
        // i32.add(base, ...) - прибавляет смещение к базовому адресу - получает абсолютный адрес элемента
        return i32.load([c.varuint32(4), 0 as any as Int], addr); // загружает значение из вычисленного адреса памяти
    }
    switch (expr.type) {
        case "num": return i32.const(expr.value);
        case "var":
            const idx = locals.indexOf(expr.name);
            if (idx === -1) throw new Error(`Undefined var: ${expr.name}`);
            return c.get_local(i32, idx);
        case "binary":
            const l = compileExpr(expr.left, locals, functionIndexMap);
            const r = compileExpr(expr.right, locals, functionIndexMap);
            switch (expr.op) {
                case "+": return i32.add(l, r);
                case "-": return i32.sub(l, r);
                case "*": return i32.mul(l, r);
                case "/": return i32.div_s(l, r);
            }
            break;
        case "neg":
            return i32.mul(i32.const(-1), compileExpr(expr.argument, locals, functionIndexMap));
    }
    throw new Error(`Unknown expr type: ${expr.type}`);
}

function compileFunctionCall(call: FunctionCall, locals: string[], functionIndexMap: Map<string, number>): Op<I32> { // компилирует вызовы функций
    const args = call.args.map(arg => compileExpr(arg, locals, functionIndexMap)); // pекурсивно компилирует все аргументы функции
    const funcIdx = functionIndexMap.get(call.name);
    if (funcIdx === undefined) throw new Error(`Unknown function: ${call.name}`);
    return c.call(i32, c.varuint32(funcIdx), args); // cоздает массив с одной инструкцией call
}

function compileArrayAccess(access: ArrayAccess, locals: string[], functionIndexMap: Map<string, number>) { // компилирует доступ к элементам массива
    const arrayIdx = locals.indexOf(access.name); // находит индекс переменной массива
    if (arrayIdx === -1) throw new Error(`Undefined array: ${access.name}`);
    const base = c.get_local(i32, arrayIdx); // загружает базовый адрес массива
    const index = compileExpr(access.index, locals, functionIndexMap); // pекурсивно компилирует выражение индекса
    const addr = i32.add(base, i32.mul(index, i32.const(4))); // вычисление абсолютного адреса
    return {
        get: () => i32.load([c.varuint32(4), 0 as any as Int], addr), // возвращает инструкцию загрузки значения из памяти
        set: (value: Op<I32>) => i32.store([c.varuint32(4), 0 as any as Int], addr, value) // возвращает инструкцию сохранения значения в память
    };
}

function compileCondition(cond: Condition, locals: string[], functionIndexMap: Map<string, number>): Op<I32> { // компилирует логические условия и сравнения
    switch (cond.type) {
        case "bool":
            return i32.const(cond.value ? 1 : 0);
        case "comp":
            const left = compileExpr(cond.left, locals, functionIndexMap);
            const right = compileExpr(cond.right, locals, functionIndexMap);
            switch (cond.op) {
                case "==": return i32.eq(left, right);
                case "!=": return i32.ne(left, right);
                case "<": return i32.lt_s(left, right);
                case "<=": return i32.le_s(left, right);
                case ">": return i32.gt_s(left, right);
                case ">=": return i32.ge_s(left, right);
            }
            break;
        case "not":
            return i32.eqz(compileCondition(cond.argument, locals, functionIndexMap));
        case "binCond":
            const l = compileCondition(cond.left, locals, functionIndexMap);
            const r = compileCondition(cond.right, locals, functionIndexMap);
            if (cond.op === "and") {
                return c.if_(i32, l, [r], [i32.const(0)]); // если l истинно, вернуть r, иначе 0
            } else if (cond.op === "or") {
                return c.if_(i32, l, [i32.const(1)], [r]); // если l истинно, вернуть 1, иначе r
            } else if (cond.op === "->") {
                return c.if_(i32, l, [r], [i32.const(1)]); // если l истинно, вернуть r, иначе 1
            }
            break;
    }
    throw new Error(`Unknown condition type: ${(cond as any).type}`);
}

function compileStatement(stmt: Statement, locals: string[], functionIndexMap: Map<string, number>): Op<Void>[] { // компилирует операторы (statements)
    const ops: Op<Void>[] = [];
    switch (stmt.type) {
        case "block":
            for (const s of stmt.statements) {
                ops.push(...compileStatement(s, locals, functionIndexMap)); // pекурсивная компиляция
            }
            break;
        case "assign":
            let values: Op<I32>[] = [];
            // if (stmt.value.type === "call") { // вызов функции
                // values = [compileFunctionCall(stmt.value, locals, functionIndexMap)];
            // } else {
                values = [compileExpr(stmt.value, locals, functionIndexMap)]; // обычные выражения
            // }
            for (let i = 0; i < stmt.targets.length; i++) {
                const targetName = stmt.targets[i];
                const targetIdx = locals.indexOf(targetName);
                if (targetIdx === -1) throw new Error(`Cannot assign to undefined: ${targetName}`);
                if (stmt.kind === "array" && stmt.indices && i === 0) { // присваивание элементу массива
                    const access = compileArrayAccess({
                        type: "arrayAccess",
                        name: targetName,
                        index: stmt.indices[0]
                    } as ArrayAccess, locals, functionIndexMap);
                    ops.push(access.set(values[0]));
                } else {
                    ops.push(c.set_local(targetIdx, values[i] || values[0])); // присваивание обычной переменной
                }
            }
            break;
        case "if":
            const cond = compileCondition(stmt.condition, locals, functionIndexMap);
            const thenOps = compileStatement(stmt.thenBranch, locals, functionIndexMap);
            const elseOps = stmt.elseBranch ? compileStatement(stmt.elseBranch, locals, functionIndexMap) : [];
            ops.push(c.void_block([c.if_(c.void, cond, thenOps, elseOps)]));
            break;
        case "while":
            const loopCond = compileCondition(stmt.condition, locals, functionIndexMap);
            const bodyOps = compileStatement(stmt.body, locals, functionIndexMap);
            const loop = c.void_loop([
                c.br_if(1, i32.eqz(loopCond)), 
                ...bodyOps,
                c.br(0) 
            ]);
            ops.push(c.void_block([loop]));
            break;
        default:
            throw new Error(`Unknown statement type: ${(stmt as any).type}`);
    }
    return ops;
}
export { FunnyError } from '../../lab08';
