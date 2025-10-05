 import { Iter, IterationNode, MatchResult } from "ohm-js";
 import grammar, { ArithmeticActionDict, ArithmeticSemantics } from "./arith.ohm-bundle";

 export const arithSemantics: ArithSemantics = grammar.createSemantics() as ArithSemantics;

 function foldChain(
     this: any,
     first: any,
     operators: IterationNode,
     rest: IterationNode,
     step: (left: number, op: string, right: number) => number
 ): number {
     const params = this.args.params;// as { [name: string]: number };
     let left = first.calculate(params) as number;
    // return rest.children.reduce((acc, child, i)=>step(acc, operators.children[i].sourceString, child.calculate(params)), left); 
     const n = operators.children.length;
     for (let i = 0; i < n; i++) {
         const op = operators.child(i).sourceString as string;
         const right = rest.child(i).calculate(params);
         left = step(left, op, right);
     }
     return left;
 }

 const arithCalc = {
     Expr(e) {
         return e.calculate(this.args.params);
     },

     Sum(first, operators, rest) {
         return foldChain.call(this, first, operators, rest, (left, op, right) =>
             op === "+" ? left + right : left - right
         );
     },

     Mul(first, operators, rest) {
         return foldChain.call(this, first, operators, rest, (left, op, right) => {
             if (op === "*") return left * right;
             if (right === 0) throw new Error("Division by zero");
             return left / right;
         });
     },

     Unary_neg(_minus, u) {
         return -u.calculate(this.args.params);
     },

     Primary_num(n) {
         return parseInt(n.sourceString, 10);
     },

     Primary_var(v) {
         const name = v.sourceString;
         if (!(name in this.args.params)) {
             return NaN;
         }
         return this.args.params[name];
     },

     Primary_parens(_open, e, _close) {
         return e.calculate(this.args.params);
     },
 } satisfies ArithmeticActionDict<number | undefined>;

 arithSemantics.addOperation<number>("calculate(params)", arithCalc);

 export interface ArithActions {
     calculate(params: { [name: string]: number }): number;
 }

 export interface ArithSemantics extends ArithmeticSemantics {
     (match: MatchResult): ArithActions;
 }
