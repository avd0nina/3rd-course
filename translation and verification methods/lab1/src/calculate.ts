import { Dict, MatchResult, Semantics } from "ohm-js";
import grammar, { AddMulActionDict } from "./addmul.ohm-bundle";

export const addMulSemantics: AddMulSemantics = grammar.createSemantics() as AddMulSemantics;

const addMulCalc = {
  Expr_plus(e, _op, t) {
    return e.calculate() + t.calculate();
  },
  Expr_minus(e, _op, t) {
    return e.calculate() - t.calculate();
  },
  Term_times(t, _op, f) {
    return t.calculate() * f.calculate();
  },
  Term_divide(t, _op, f) {
    return t.calculate() / f.calculate();
  },
  Factor_parens(_l, e, _r) {
    return e.calculate();
  },
  number(_digits) {
    return parseInt(this.sourceString, 10);
  }
} satisfies AddMulActionDict<number>;

addMulSemantics.addOperation<number>("calculate()", addMulCalc);

interface AddMulDict extends Dict {
  calculate(): number;
}

interface AddMulSemantics extends Semantics {
  (match: MatchResult): AddMulDict;
}
