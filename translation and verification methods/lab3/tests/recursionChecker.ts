import { Alt, Grammar, PExpr, Seq } from 'ohm-js';

export function findLeftRecursion(g: Grammar, rule?: PExpr | string, stack?: string[]): string[] | undefined
{
  if (rule == undefined)
    rule = ((g as any).defaultStartRule as string);
  
  stack ??= [];
  if(typeof rule === "string")
  {
    const lastMention = stack.lastIndexOf(rule);
    if (lastMention >= 0)
      return stack.slice(lastMention);
  
    stack.push(rule);
    try {
      return findLeftRecursion(g, g.rules[rule].body, stack);
    }
    finally {
      stack.pop();
    }
  }
  switch(rule.constructor.name)
  {
    case "Apply": return findLeftRecursion(g, (rule as any).ruleName as string, stack);
    case "Seq": {
      let factors = (rule as Seq).factors;
      return (factors.length > 0) 
        ? findLeftRecursion(g, factors[0], stack)
        : undefined;
    }
    case "Alt": 
    {
      for(var term of (rule as Alt).terms)
      {
        const r = findLeftRecursion(g, term, stack);
        if(r)
          return r;
      }
      break;
    }
    case "Plus":
    case "Star":
    case "Opt":
    case "Not": 
       return findLeftRecursion(g, (rule as any).expr as PExpr, stack);
  }
  return undefined;
}
