import { Dict, MatchResult, Semantics, Node, IterationNode } from "ohm-js";
import grammar, { AddMulActionDict } from "./addmul.ohm-bundle";

export const addMulSemantics: AddMulSemantics = grammar.createSemantics() as AddMulSemantics;

const addMulCalc = {
  Expr(e: Node) {
    return e.calculate();
  },
  Add(left: Node, ops: IterationNode, rights: IterationNode) {
    let result = left.calculate();
    for (let i = 0; i < ops.numChildren; i++) {
      result += rights.child(i).calculate();
    }
    return result;
  },
  Mul(left: Node, ops: IterationNode, rights: IterationNode) {
    let result = left.calculate();
    for (let i = 0; i < ops.numChildren; i++) {
      result *= rights.child(i).calculate();
    }
    return result;
  },
  Primary(n: Node) {
    return n.calculate();
  },
  Paren(_l: Node, expr: Node, _r: Node) {
    return expr.calculate();
  },
  number(digits: Node) {
    return parseInt(digits.sourceString, 10);
  }
} satisfies AddMulActionDict<number>;

addMulSemantics.addOperation<Number>("calculate()", addMulCalc);

interface AddMulDict extends Dict {
    calculate(): number;
}

interface AddMulSemantics extends Semantics {
    (match: MatchResult): AddMulDict;
}
