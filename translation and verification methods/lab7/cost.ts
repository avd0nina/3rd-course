import { Expr } from "../../lab04";

export function cost(e: Expr): number {
    switch (e.type) {
        case "num":
            return 0;
        case "var":
            return 1;
        case "neg":
            return 1 + cost(e.arg);
        case "bin":
            return 1 + cost(e.left) + cost(e.right);
    }
}
