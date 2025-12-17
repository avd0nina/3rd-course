import { test } from '../../mark';
import { evaluate, maxStackDepth, SyntaxError } from '../src';
  
describe('testing addition and multiplication', () => {
    test("Empty expression is invalid", 3, evaluate, SyntaxError, "");
    test("Number is a valid expression", 3, evaluate, 42, "42");
    test("Numbers with spaces are invalid", 3, evaluate, SyntaxError, "42 7");
    test("Addition is a valid expression", 3, evaluate, 42, "35 7 +");
    test("Incomplete addition is invalid", 3, evaluate, SyntaxError, "42 +");
    test("Standalone + is invalid", 3, evaluate, SyntaxError, "+ 42");
    test("Unbalanced pluses are invalid", 3, evaluate, SyntaxError, "7++35");
    test("Spaces are permitted in the addition", 3, evaluate, 42, "  35 7 +");
    test("Tabs are permitted in the addition", 3, evaluate, 42, "7\t35 +");
    test("Newlines are permitted in the addition", 3, evaluate, 42, `
        35 
        7 +`);
    test("Multiple additions are valid", 3, evaluate, 42, "5 4 3 ++ 2+ 1+ 2 3 + 4+5+6+7+ +");
    
    test("Multiplication is a valid expression", 3, evaluate, 42, "6 7 *");
    test("Incomplete multiplication is invalid", 3, evaluate, SyntaxError, "42 *");
    test("Standalone * is invalid", 3, evaluate, SyntaxError, "* 42");
});

describe("testing stack depth", () => {
    test("stack depth of one", 4, maxStackDepth, 3, "3 4 * 5 6 * +");
    test("stack depth of two", 4, maxStackDepth, 2, "4 2 +");
    test("stack depth of three", 4, maxStackDepth, 3, "4 2 1 + +");
    test("stack depth of two (1)", 4, maxStackDepth, 2, "4 2 + 1 +");
    test("stack depth of many", 4, maxStackDepth, 3, "5 4 3 ++ 2+ 1+ 2 3 + 4+5+6+7+ +");
    test("stack depth of five", 4, maxStackDepth, 5, "5 4 3 2+*+ 1+ 2 3 4 5 + + 6 7 + * + *");
});
