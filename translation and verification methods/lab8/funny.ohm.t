Funny <: Arithmetic {
    Module = FunctionDef+

    FunctionDef = ident "(" ParameterList? ")" ("requires" Predicate)? "returns" ParameterList ("ensures" Predicate)? ("uses" LocalsList)? Statement
    
    space += comment
    
    comment = "//" (~"\n" any)* ("\n" | end)

    ParameterList = VariableDef ("," VariableDef)*
    LocalsList = LocalDef ("," LocalDef)*
    
    VariableDef = ident ":" Type
    LocalDef = ident ":" "int"
    
    Type = "int" "[]"  -- array
         | "int"       -- int
    
    Statement = Block
              | Conditional
              | While  
              | Assignment
    
    Block = "{" Statement* "}"
    
    Conditional = "if" "(" Condition ")" Statement ("else" Statement)?
    
    While = "while" "(" Condition ")" ("invariant" Predicate)? Statement
    
    Assignment = AssignmentTarget "=" Expr ";"                                      -- simple
               | ident "[" Expr "]" "=" Expr ";"                                    -- array
               | ident ("," ident)+ "=" FunctionCall ";"                            -- tuple
    
    AssignmentTarget = ident
    
    Condition = ImpliesCondition
    
     ImpliesCondition = OrCondition "->" ImpliesCondition  -- implies
                    | OrCondition
     
     OrCondition = OrCondition "or" AndCondition  -- or
               | AndCondition
     
     AndCondition = AndCondition "and" NotCondition  -- and
               | NotCondition
     
     NotCondition = "not" NotCondition  -- not
               | PrimaryCondition
     
     PrimaryCondition = "true"             -- true
                    | "false"            -- false
                    | Comparison         -- comp
                    | "(" Condition ")"  -- paren
    
    Comparison = Expr CompOp Expr
    
    CompOp = "==" | "!=" | "<=" | ">=" | "<" | ">"
    
    Predicate = OrPredicate
    
    OrPredicate = OrPredicate "or" AndPredicate  -- or
                | AndPredicate
    
    AndPredicate = AndPredicate "and" ImpliesPredicate  -- and
                 | ImpliesPredicate
    
    ImpliesPredicate = ImpliesPredicate "->" NotPredicate  -- implies
                     | NotPredicate
    
    NotPredicate = "not" NotPredicate  -- not
                 | PrimaryPredicate
    
    PrimaryPredicate = "true"                  -- true
                     | "false"                 -- false
                     | Comparison              -- comp
                     | Quantifier              -- quant
                     | FormulaRef              -- formula
                     | "(" Predicate ")"       -- paren
    
    Quantifier = ("forall" | "exists") "(" VariableDef "|" Predicate ")"
    
    FormulaRef = ident "(" ListOf<Expr, ","> ")"
    
    PrimaryExpr := "(" Expr ")"     -- paren
                 | FunctionCall     -- call
                 | ArrayAccess      -- array
                 | number           -- num
                 | ident            -- var
    
    FunctionCall = ident "(" ListOf<Expr, ","> ")"
    
    ArrayAccess = ident "[" Expr "]"
    
    variable := ident
    
    ident = ~keyword letter (letter | digit)*
    
    keyword = ("if" | "else" | "while" | "returns" | "uses" | "requires" | "ensures" 
             | "invariant" | "true" | "false" | "not" | "and" | "or" 
             | "forall" | "exists" | "int") ~(letter | digit)
}
