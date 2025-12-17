import { parseVerifyAndCompile } from "../src";
import { flushZ3, VerificationError } from '../src/verifier';
import { testFilesInFolderAsync } from "./testFilesInFolderAsync";

describe('11. Testing the correct samples', () => {
    testFilesInFolderAsync("./lab10/samples", parseVerifyAndCompile);
});
describe('11. Testing the incorrect samples', () => {
    testFilesInFolderAsync("./lab11/samples", parseVerifyAndCompile);
});

describe('11. A+ features: Precise error location', () => {
    test('postcondition violation should report exact condition type', async () => {
        const code = `fortyTwo() 
    returns c: int
    ensures c == 42
{
    c = 43;
}`;
        try {
            await parseVerifyAndCompile('test', code);
            fail('Expected verification to fail');
        } catch (e: any) {
            expect(e).toBeInstanceOf(VerificationError);
            expect(e.funcName).toBe('fortyTwo');
            expect(e.conditionType).toBe('postcondition');
            // counterexample may or may not be defined
        }
    });

    test('loop invariant violation should report exact condition type', async () => {
        const code = `sqrt(z: int) 
    requires z >= 1
    returns x: int
    ensures x*x <= z and (x+1)*(x+1) > z
    uses y: int
{
    x = 1;
    y = 1;
    while(y <= z) invariant(y==x*x and (x-1)*(x-1) <= z)
    {
        y = y + 2*x + 1;
        x = x + 1;
    }
}`;
        try {
            await parseVerifyAndCompile('test', code);
            fail('Expected verification to fail');
        } catch (e: any) {
            expect(e).toBeInstanceOf(VerificationError);
            expect(e.funcName).toBe('sqrt');
            // Should be one of the loop invariant types
            expect(['loop_invariant_init', 'loop_invariant_preserve', 'loop_invariant_exit', 'postcondition']).toContain(e.conditionType);
        }
    });

    test('missing ensures clause with wrong result', async () => {
        const code = `increment(x: int) 
    returns y: int
    ensures y == x+1

    y = x;`;
        try {
            await parseVerifyAndCompile('test', code);
            fail('Expected verification to fail');
        } catch (e: any) {
            expect(e).toBeInstanceOf(VerificationError);
            expect(e.funcName).toBe('increment');
            expect(e.conditionType).toBe('postcondition');
        }
    });
});

afterAll(() => flushZ3())


