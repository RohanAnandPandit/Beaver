# -*- coding: utf-8 -*-
"""
Created on Mon Jun 29 11:20:51 2020

@author: rohan
"""
from Types import String
functionNamesIO = ['input', 'printLn', 'print']

def printLn(a, program_state):
    print_(a, program_state)
    print('')
    return String(a)

def print_(a, program_state):
    a = a.simplify(program_state)
    if isinstance(a, String):
        print(str(a)[1:-1], end = '')
    else:
        print(str(a), end = '')
    return String(a)

def show(a, program_state):
    return String(str(a))

def input_(question):
    inp = input(question.value)
    return String(inp)