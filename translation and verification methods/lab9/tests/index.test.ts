import { readFileSync } from "fs";
import { join as pathJoin } from 'path';
import { test } from "../../mark";
import { parseAndCompile } from "../src";

const sampleDir = "./lab08/samples";


async function testOneResult<T = number>(fileName: string, funcName: string, ...args: number[]): Promise<T>
{
    const module = await parseAndCompile(fileName, readFileSync(pathJoin(sampleDir, fileName+'.funny'), 'utf-8'));
    return module[funcName](...args);
}

async function testTwoResults<T = number>(fileName: string, funcName: string, ...args: number[]): Promise<[T, T]>
{
    const module = await parseAndCompile(fileName, readFileSync(pathJoin(sampleDir, fileName+'.funny'), 'utf-8'));
    return module[funcName](...args);
}

describe('Testing the sample programs', () => {
    test('constant', 3, testOneResult<number>, 42, '3.fortyTwo', 'fortyTwo');
    test('local var usage', 3, testOneResult<number>, 42, '3.functionWithLocals', 'foo', 10, 4);
    test('increment', 3, testOneResult<number>, 42, '3.increment', 'increment', 41);
    test('expression', 3, testOneResult<number>, 42, '3.sixBySeven', 'sixBySeven');
    test('call', 4, testOneResult<number>, 86, '4.call', 'bar', 2);
    test('loop', 4, testOneResult<number>, 40, '4.loop', 'multiply', 4);
    test('two constants', 4, testTwoResults<number>, [6, 7], '4.twoConsts', 'sixAndSeven');
    test('two results', 4, testTwoResults<number>, [6, 0], '4.divide', 'divide', 42, 7);
    test('conditional', 4, testOneResult<number>, 7, '4.gcd', 'gcd', 42, 49);
});


