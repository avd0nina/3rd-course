Funnier <: Funny {
    FunctionDef := ident "(" ParameterList? ")" ("requires" Predicate)? "returns" ReturnSpec ("ensures" Predicate)? ("uses" LocalsList)? Statement
    
    ReturnSpec = "void"  -- void
               | ParameterList  -- params
    
    Statement := Block
              | Conditional
              | While
              | FunctionCallStatement
              | Assignment
    
    FunctionCallStatement = FunctionCall ";"
    
    While := "while" "(" Condition ")" ("invariant" "(" Predicate ")")? Statement
}
