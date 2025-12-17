import { evaluate, SyntaxError } from '../src';
import { test } from '../../mark';
  
export function syncFail()
{
    throw new Error("oops");
}

describe('testing addition and multiplication', () => {
    test("Empty expression is invalid", 3, evaluate, SyntaxError, '');
    test("Number is a valid expression", 3, evaluate, 42, "42");
    test("Numbers with spaces are invalid", 3, evaluate, SyntaxError, "42 7");
    test("Addition is a valid expression", 3, evaluate, 42, "35+7");
    test("Incomplete addition is invalid", 3, evaluate, SyntaxError, "42+");
    test("Standalone + is invalid", 3, evaluate, SyntaxError, "+42");
    test("Sequential pluses are invalid", 3, evaluate, SyntaxError, "7++35");
    test("Spaces are permitted in the addition", 4, evaluate, 42, "  35 +7");
    test("Tabs are permitted in the addition", 4, evaluate, 42, "7\t+35");
    test("Newlines are permitted in the addition", 4, evaluate, 42, `
        35  +
        7`);
    test("Multiple additions are valid", 3, evaluate, 42, "5+4+3+2+1+2+3+4+5+6+7");
    
    test("Multiplication is a valid expression", 3, evaluate, 42, "6*7");
    test("Incomplete multiplication is invalid", 3, evaluate, SyntaxError, "42*");
    test("Standalone * is invalid", 3, evaluate, SyntaxError, "*42");
    test("Multiplication is performed before addition", 4, evaluate, 42, "7+4*7+7");

    test("Complex expressions are supported", 4, evaluate, 42, "7+2*7+3*6+3");
    test("Parentheses are correctly supported", 4, evaluate, 42, "(2+1)*7+(3*2*3)+2*(1+0)+1");
    test("Extra paren are ok", 4, evaluate, 42, "(2+1)*7+(3*(2)*3)+2*((1+(0)))+1");
});
