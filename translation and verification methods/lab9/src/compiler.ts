import { writeFileSync } from "fs";
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

//компилирует модуль Funny в WebAssembly модуль
export async function compileModule<M extends Module>(m: M, name?: string): Promise<WebAssembly.Exports> {
    const typeSection: any[] = [];
    const functionSection: any[] = [];
    const exportSection: ExportEntry[] = [];
    const codeSection: any[] = [];
    const functionIndexMap = new Map<string, number>();

    // 1. Создаём типы функций и экспорты
    // 1. Создаём типы функций и экспорты
for (let i = 0; i < m.functions.length; i++) {
    const func = m.functions[i];
    functionIndexMap.set(func.name, i);

    const paramTypes = func.parameters.map(() => i32);
    const returnTypes = func.returns.map(() => i32);

    typeSection.push(c.func_type_m(paramTypes, returnTypes));
    functionSection.push(c.varuint32(i));

    // ← ИСПРАВЛЕНО: второй аргумент — external_kind.function
    exportSection.push(
        c.export_entry(
            c.str_ascii(func.name),
            c.external_kind.function,   // 0
            c.varuint32(i)
        )
    );
}

    // 2. Генерация тел функций
    for (let i = 0; i < m.functions.length; i++) {
        const func = m.functions[i];
        const allLocals: string[] = [
            ...func.parameters.map(p => p.name),
            ...func.returns.map(r => r.name),
            ...func.locals.map(l => l.name)
        ];

        // Все локальные переменные — i32 (включая массивы — хранятся как указатели)
        const localEntries: LocalEntry[] = [
            c.local_entry(c.varuint32(allLocals.length), i32)
        ];

        const bodyOps: (Op<Void> | Op<I32>)[] = compileStatement(func.body, allLocals, functionIndexMap);

        // Возвращаем значения возвращаемых переменных
        for (const ret of func.returns) {
            const idx = allLocals.indexOf(ret.name);
            bodyOps.push(c.get_local(i32, idx));
        }

        codeSection.push(c.function_body(localEntries, bodyOps));
    }

    const mod = c.module([
        c.type_section(typeSection),
        c.function_section(functionSection),
        c.export_section(exportSection),
        c.code_section(codeSection)
    ]);

    const emitter = new BufferedEmitter(new ArrayBuffer(mod.z));
    mod.emit(emitter);

    const wasmModule = await WebAssembly.instantiate(emitter.buffer);
    return wasmModule.instance.exports;
}

//компилирует арифметическое выражение в Wasm инструкции
function compileExpr(expr: any, locals: string[], functionIndexMap: Map<string, number>): Op<I32> {
    // 1. Вызов функции
    if (expr.type === "call") {
        const args = expr.args.map((a: any) => compileExpr(a, locals, functionIndexMap));
        const idx = functionIndexMap.get(expr.name);
        if (idx === undefined) throw new Error(`Unknown function: ${expr.name}`);
        return c.call(i32, c.varuint32(idx), args);
    }

    // 2. Доступ к массиву
    if (expr.type === "arrayAccess") {
        const base = c.get_local(i32, locals.indexOf(expr.name));
        const index = compileExpr(expr.index, locals, functionIndexMap);
        const addr = i32.add(base, i32.mul(index, i32.const(4)));
        return i32.load([c.varuint32(4), 0 as any as Int], addr);
    }

    // 3. Обычные арифметические выражения
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

//компилирует вызов функции с аргументами
function compileFunctionCall(call: FunctionCall, locals: string[], functionIndexMap: Map<string, number>): Op<I32>[] {
    const args = call.args.map(arg => compileExpr(arg, locals, functionIndexMap));
    const funcIdx = functionIndexMap.get(call.name);
    if (funcIdx === undefined) throw new Error(`Unknown function: ${call.name}`);
    return [c.call(i32, c.varuint32(funcIdx), args)];
}

//компилирует доступ к элементу массива по индексу
function compileArrayAccess(access: ArrayAccess, locals: string[], functionIndexMap: Map<string, number>) {
    const arrayIdx = locals.indexOf(access.name);
    if (arrayIdx === -1) throw new Error(`Undefined array: ${access.name}`);

    const base = c.get_local(i32, arrayIdx);
    const index = compileExpr(access.index, locals, functionIndexMap);
    const offset = i32.mul(index, i32.const(4));
    const addr = i32.add(base, offset);

    return {
        get: () => i32.load([c.varuint32(4), 0 as any as Int], addr),
        set: (value: Op<I32>) => i32.store([c.varuint32(4), 0 as any as Int], addr, value)
    };
}

//компилирует условное выражение в Wasm инструкции сравнения
function compileCondition(cond: Condition, locals: string[], functionIndexMap: Map<string, number>): Op<I32> {
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
                return c.if_(i32, l, [r], [i32.const(0)]);
            } else if (cond.op === "or") {
                return c.if_(i32, l, [i32.const(1)], [r]);
            } else if (cond.op === "->") {
                return c.if_(i32, l, [r], [i32.const(1)]);
            }
            break;
    }
    throw new Error(`Unknown condition type: ${(cond as any).type}`);
}

//компилирует операторы (блоки, присваивания, условия, циклы) в Wasm инструкции
function compileStatement(stmt: Statement | any, locals: string[], functionIndexMap: Map<string, number>): Op<Void>[] {
    const ops: Op<Void>[] = [];

    switch (stmt.type) {
        case "block":
            for (const s of stmt.statements) {
                ops.push(...compileStatement(s, locals, functionIndexMap));
            }
            break;
        
        case "callStmt":
            compileFunctionCall(stmt.call, locals, functionIndexMap);
            break;

        case "assign":
            // Правая часть — либо выражение, либо вызов функции
            let values: Op<I32>[] = [];

            if (stmt.value.type === "call") {
                values = compileFunctionCall(stmt.value, locals, functionIndexMap);
            } else {
                values = [compileExpr(stmt.value as arith.Expr, locals, functionIndexMap)];
            }

            // Левая часть — targets + indices (для массивов)
            for (let i = 0; i < stmt.targets.length; i++) {
                const targetName = stmt.targets[i];
                const targetIdx = locals.indexOf(targetName);
                if (targetIdx === -1) throw new Error(`Cannot assign to undefined: ${targetName}`);

                if (stmt.kind === "array" && stmt.indices && i === 0) {
                    const access = compileArrayAccess({
                        type: "arrayAccess",
                        name: targetName,
                        index: stmt.indices[0]
                    } as ArrayAccess, locals, functionIndexMap);
                    ops.push(access.set(values[0]));
                } else {
                    ops.push(c.set_local(targetIdx, values[i] || values[0]));
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
                c.br_if(1, i32.eqz(loopCond)), // если условие ложно — выход
                ...bodyOps,
                c.br(0) // повтор цикла
            ]);

            ops.push(c.void_block([loop]));
            break;

        default:
            throw new Error(`Unknown statement type: ${(stmt as any).type}`);
    }

    return ops;
}

export { FunnyError } from '../../lab08';
