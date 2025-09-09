# Лабораторная работа 06: Символьное дифференцирование

Это упражнение основывается на AST из лабораторной работы 04 to build a tiny symbolic calculator capable of performing a partial derivation of a multi-argument function

## Goal

In this lab we will practice transforming the Abstract Syntax Trees. Even though the real-world compilers don't usually support the symbolic algebra like deriving the functions, the transformations performed there do have a few similarities to the one implemented in this lab.

From the mathematics standpoint, derivation is an example of a Higher-Order Function ([HOF](https://en.wikipedia.org/wiki/Higher-order_function)): it accepts for an argument and returns a *function* instead of a *value*.  

However, in the code it looks like a regular function, since the functions it operates upon are represented in a *symbolic* form - as we've previously discussed, `Expr` instance can be seen as a function of several variables.

Now, we're going to build a *partial derivative* of this function in respect to the specified variable.
In order to verify the results, we would also compile this function using the results of [Lab05](../lab05/README.md) and check the value in a few points.

## Tasks

1. Implement the function `derive` in [derive.ts](src/derive.ts) that performs a partial symbolic derivation
2. Improve this function by adding a few obvious simplification steps

## Evaluation

- C | 3 | Hey, Not Too Rough:
  - Implement the derivation of addition, subtraction, division, multiplication, and negation
- B | 4 | Hurt Me Plenty:
  - Reduce the resulting expressions using the following identities:
    - `x * 0 = 0 * x = 0`
    - `x * 1 = 1 * x = x`
    - `x / 1 = x`
    - `x + 0 = 0 + x = x`
    - `x - 0 = x`
    - `0 - x = -x`
    - `--x = x`
- A | 5 | Ultra-Violence:
  - Reduce the resulting expressions by expanding all the factors and collecting all the terms
  
