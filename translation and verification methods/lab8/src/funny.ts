import * as arith from "../../lab04";

export interface Module
{
    type: 'module';
    functions: FunctionDef[]
}
//определение функции
export interface FunctionDef
{
    type: 'fun';
    name: string;
    parameters: ParameterDef[];
    returns: ParameterDef[];
    locals: ParameterDef[];
    body: Statement;
}

//опр параметра, локальной переменной или возвращаемого значения
export interface ParameterDef
{
    type: "param";
    name: string;
    varType: VarType;
}

//число или массив чисел
export type VarType = 'int' | 'int[]';

//присваивание, блок, условный оператор или цикл while
export type Statement = Assignment | Block | Conditional | While;

//оператор присваивания, kind определяет тип присваивания
export interface Assignment
{
    type: 'assign';
    kind: 'simple' | 'array' | 'tuple';
    targets: string[];
    indices?: arith.Expr[];
    value: arith.Expr | FunctionCall;
}

//блок операторов в {}
export interface Block
{
    type: 'block';
    statements: Statement[];
}

export interface Conditional
{
    type: 'if';
    condition: Condition;
    thenBranch: Statement;
    elseBranch?: Statement;
}

//while с условием и телом
export interface While
{
    type: 'while';
    condition: Condition;
    body: Statement;
}

//тип условия 
export type Condition = BoolLiteral | Comparison | NotCondition | BinaryCondition;

export interface BoolLiteral
{
    type: 'bool';
    value: boolean;
}

export interface Comparison
{
    type: 'comp';
    op: '==' | '!=' | '<' | '<=' | '>' | '>=';
    left: arith.Expr;
    right: arith.Expr;
}

export interface NotCondition
{
    type: 'not';
    argument: Condition;
}

export interface BinaryCondition
{
    type: 'binCond';
    op: 'and' | 'or' | '->';
    left: Condition;
    right: Condition;
}

//вызов функции с аргументами
export interface FunctionCall
{
    type: 'call';
    name: string;
    args: arith.Expr[];
}

//доступ к элементу массива по индексу
export interface ArrayAccess
{
    type: 'arrayAccess';
    name: string;
    index: arith.Expr;
}
