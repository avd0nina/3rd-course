import { parseExpr } from "./parser";
import { printExpr } from "./printExpr";

export * from "./printExpr";
export * from "./ast";
export * from "./parser";

export const parseAndPrint = (source: string): string => printExpr(parseExpr(source));
