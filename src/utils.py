# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 11:24:28 2020

@author: rohan
"""
import IO
import Prelude
from Types import (Variable, Int, Float, Bool, EnumValue, Object, Structure,
                   Char, Type, Class, Struct, String, Null)
from List import Nil, Cons, head, tail, Array, List
from Tuple import functionNamesTuple, Tuple
from HFunction import Func

def isPrimitive(expr):
    return type(expr) in [Int, Float, Bool, Char, String, EnumValue, Null]

def null(expr):
    return isinstance(expr, Null)

def isList(expr):
    if issubclass(type(expr), List):
        return True
    if isinstance(expr, Object):
        for interface in expr.class_.interfaces:
            if interface.name == 'List':
                return True
    return False

def patternMatch(expr1, expr2, program_state):
    from Operator_Functions import equals 
    from Expression import BinaryExpr

    expr2 = expr2.simplify(program_state)
    
    if isPrimitive(expr1) and isPrimitive(expr2):
        return equals(expr1.simplify(program_state), expr2, program_state).value
    
    if isinstance(expr1, Variable):
        if isinstance(expr1.simplify(program_state), Type):
            return (isinstance(expr2, (Type, Class, Struct)) and 
                    expr1.simplify(program_state).name == expr2.name)
        return True
    
    if isinstance(expr1, BinaryExpr) and expr1.operator.name == '@':
        return patternMatch(expr1.expr, expr2, program_state)
        
    if isinstance(expr1, Nil) and isinstance(expr2, Nil):
        return True 
    
    if isinstance(expr1, Cons):
        if isinstance(expr2, Nil): 
            return False
        return (patternMatch(head(expr1), head(expr2).simplify(program_state), program_state) 
                and patternMatch(tail(expr1), tail(expr2), program_state))  

    if (isinstance(expr1, BinaryExpr) and expr1.operator.name == ':' and 
        isList(expr2)):
        if isinstance(expr2, Nil):
            return False
        return (patternMatch(expr1.leftExpr, head(expr2, program_state).simplify(program_state), program_state) 
                and patternMatch(expr1.rightExpr, tail(expr2, program_state), program_state))    
    
    if type(expr1) == type(expr2) and type(expr1) in (Tuple, Array):
        if len(expr1.items) == len(expr2.items) == 0:
            return True
        
        if len(expr1.items) != len(expr2.items):
            if len(expr1.items) == 0:
                return False
            if (isinstance(expr1.items[-1], Variable) and 
                expr1.items[-1].name == '...'):
                if len(expr1.items) - 1 > len(expr2.items):
                    return False
            else:
                return False
            
        if (len(expr1.items) > 0 and isinstance(expr1.items[0], Variable) and 
              expr1.items[0].name == '...'):
            return True
        
        return (patternMatch(expr1.items[0],
                             expr2.items[0].simplify(program_state),
                             program_state) and
                patternMatch(Tuple(expr1.items[1:], program_state),
                             Tuple(expr2.items[1:], program_state),
                             program_state)) 

    if isinstance(expr1, BinaryExpr) and expr1.operator.name == " ": 
        if typeMatch(expr1.leftExpr, expr2, program_state):
            if isinstance(expr2, Structure):
                return patternMatch(expr1.rightExpr, Tuple(expr2.values),
                                    program_state) 
            else:
                return patternMatch(expr1.rightExpr, expr2, program_state)
    else:
        return equals(expr1.simplify(program_state), expr2, program_state).value

    return False 

def typeMatch(type_, expr, program_state):
    from Types import Type, Union
    if (null(type_.simplify(program_state)) or 
        null(expr.simplify(program_state))):
        return True 
    
    if isinstance(type_, Variable) or isinstance(type_, Type):
        if type_.name == 'var':
            return True
        
        if type_.name == 'Type':
            return program_state.isType(expr)

        elif type_.name == 'Object':
            return isinstance(expr, Object)
        
        elif isinstance(expr, Object):
            return type_.simplify(program_state).name == expr.class_.name
        
        elif type_.name == 'Func':
            return issubclass(type(expr), Func)
        
        elif isinstance(type_.simplify(program_state), Type):
            if isPrimitive(expr):
                return type_.simplify(program_state).name == expr.type 
            if type_.simplify(program_state).name in ('int', 'float', 'char',
                             'string', 'bool'):
                return False
            return typeMatch(type_.simplify(program_state).expr, expr, 
                             program_state)

        elif isinstance(type_.simplify(program_state), Union):
            type_ = type_.simplify(program_state)
            for t in type_.types:
                if typeMatch(t, expr, program_state):
                    return True
                
        elif isinstance(expr, Structure):
            return type_.name == expr.type.name


    elif isinstance(type_, Nil) and isList(expr):
        return True
    
    elif isinstance(type_, Cons) and isList(expr):
        return (typeMatch(head(type_, program_state), head(expr, program_state), program_state) 
                and typeMatch(tail(type_, program_state), tail(expr, program_state), program_state))

    if (type(expr) in (Tuple, Array) and isinstance(type_, Variable) and
        type_.name == '...'): 
        return True
    
    elif type(type_) == type(expr) and type(type_) in (Tuple, Array):
        if len(type_.items) == 0:
            return True
        
        elif (isinstance(type_.items[0], Variable) and 
              type_.items[0].name == '...'):
            return True
        
        elif len(type_.items) != len(expr.items):
            if (isinstance(type_.items[-1], Variable) and 
                type_.items[-1].name == '...'):
                if len(type_.items) - 1 > len(expr.items):
                    return False
            else:
                return False
        return (typeMatch(type_.items[0], expr.items[0]) and
                typeMatch(Tuple(type_.items[1:], program_state), Tuple(expr.items[1:], program_state)))
        
    return False
    
def optimise(expr):
    from Expression import BinaryExpr
    from Operator_Functions import equals
    if isinstance(expr, BinaryExpr):
        expr.leftExpr = optimise(expr.leftExpr)
        expr.rightExpr = optimise(expr.rightExpr)
        if expr.operator.name in ('+', '||'):
            if equals(expr.leftExpr, Int(0)).value:
                if expr.rightExpr != None:
                    return expr.rightExpr
            elif equals(expr.rightExpr, Int(0)).value:
                if expr.leftExpr != None:
                    return expr.leftExpr
        elif expr.operator.name == '-':
                if equals(expr.rightExpr, Int(0)).value:
                    if (expr.leftExpr != None):
                        return expr.leftExpr
        elif expr.operator.name == '*':
            if equals(expr.leftExpr, Int(0)).value:
                if expr.rightExpr != None:
                    return Int(0) 
            elif equals(expr.rightExpr, Int(0)).value:
                if expr.leftExpr != None:
                    return Int(0)
            elif equals(expr.leftExpr, Int(1)).value:
                if expr.rightExpr != None:
                    return expr.rightExpr
            elif equals(expr.rightExpr, Int(1)).value:
                if expr.leftExpr != None:
                    return expr.leftExpr
        elif expr.operator.name == '&&':
            if equals(expr.leftExpr, Int(0)).value:
                if expr.rightExpr != None:
                    return Bool(False)
            elif equals(expr.rightExpr, Int(0)).value:
                if expr.leftExpr != None:
                    return Bool(False)
        elif expr.operator.name == '/':
            if equals(expr.leftExpr, Int(0)).value:
                if expr.rightExpr != None:
                    return Int(0)
            elif equals(expr.rightExpr, Int(1)).value:
                if expr.leftExpr != None:
                    return expr.leftExpr
        elif expr.operator.name == '^':
            if equals(expr.leftExpr, Int(1)).value:
                if expr.rightExpr != None:
                    return Int(1)
            elif equals(expr.leftExpr, Int(0)).value:
                if expr.rightExpr != None:
                    return Int(0)
            elif equals(expr.rightExpr, Int(1)).value:
                if expr.leftExpr != None:
                    return expr.leftExpr
            elif equals(expr.rightExpr, Int(0)).value:
                if expr.leftExpr != None:
                    return Int(1)
        elif expr.operator.name == '++':
            if isinstance(expr.leftExpr, Nil):
                if expr.rightExpr != None:
                    return expr.rightExpr
            elif isinstance(expr.rightExpr, Nil):
                if expr.leftExpr != None:
                    return expr.leftExpr

    return expr

def replaceVariables(expr, program_state):
    from Expression import BinaryExpr
    from Types import Collection
    if isinstance(expr, Variable):
        expr = expr.simplify(program_state)
    elif isinstance(expr, BinaryExpr):
        left = expr.leftExpr
        if expr.operator.name not in ('=', 'where'):
            left = replaceVariables(expr.leftExpr, program_state)
        right = replaceVariables(expr.rightExpr, program_state)
        expr = BinaryExpr(expr.operator, left, right)
    elif isinstance(expr, Cons):
        expr = Cons(replaceVariables(expr.item, program_state),
                    replaceVariables(expr.tail, program_state), program_state)
    elif isinstance(expr, Tuple):
        expr = Tuple(list(map(lambda exp: replaceVariables(exp, program_state),
                              expr.tup)), program_state)
    elif isinstance(expr, Collection):
        expr = Collection(list(map(lambda exp: replaceVariables(exp, program_state),
                                   expr.items)), expr.operator)        
    return expr

def convertToList(expr, program_state):
    # If None is returned means there was no operand or 
    # operator which means it is an empty list
    xs = Nil()
    for i in range(len(expr) - 1, -1, -1):
        xs = Cons(expr[i], xs, program_state)
    return xs