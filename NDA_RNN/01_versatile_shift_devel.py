#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 26 12:54:07 2025

@author: gelenag
"""

from collections import deque

#%% TM Description
# Binary Adder Turing Machine
states = ['q0', 'q1',  'q2',  'q3',  'q4',  'q5', 'q6',  'q7',  'q8',  'q9', 'end']
symbols = ['#', '0', '1', 'A', 'B']
transitions = {('q0', '#'): ('q0', '#', 'R'),
               ('q0', '0'): ('q1', '0', 'R'),
               ('q0', '1'): ('q1', '1', 'R'),
               ('q1', '#'): ('q2', '#', 'R'),
               ('q1', '0'): ('q1', '0', 'R'),
               ('q1', '1'): ('q1', '1', 'R'),
               ('q1', 'A'): ('q1', 'A', 'R'),
               ('q1', 'B'): ('q1', 'B', 'R'),
               ('q2', '#'): ('q3', '#', 'L'),
               ('q2', '0'): ('q2', '0', 'R'),
               ('q2', '1'): ('q2', '1', 'R'),
               ('q3', '#'): ('q9', '#', 'L'),
               ('q3', '0'): ('q4', '#', 'L'),
               ('q3', '1'): ('q6', '#', 'L'),
               ('q4', '#'): ('q5', '#', 'L'),
               ('q4', '0'): ('q4', '0', 'L'),
               ('q4', '1'): ('q4', '1', 'L'),
               ('q5', 'A'): ('q5', 'A', 'L'),
               ('q5', 'B'): ('q5', 'B', 'L'),
               ('q5', '0'): ('q1', 'A', 'R'),
               ('q5', '1'): ('q1', 'B', 'R'),
               ('q6', '0'): ('q6', '0', 'L'),
               ('q6', '1'): ('q6', '1', 'L'),
               ('q6', '#'): ('q7', '#', 'L'),
               ('q7', 'A'): ('q7', 'A', 'L'),
               ('q7', 'B'): ('q7', 'B', 'L'),
               ('q7', '0'): ('q1', 'B', 'R'),
               ('q7', '1'): ('q8', 'A', 'L'),
               ('q8', '1'): ('q8', '0', 'L'),
               ('q8', '0'): ('q1', '1', 'R'),
               ('q8', '#'): ('q1', '1', 'R'),
               ('q9', 'A'): ('q9', '0', 'L'),
               ('q9', 'B'): ('q9', '1', 'L'),
               ('q9', '#'): ('end', '#', 'R'),
               ('q9', '0'): ('end', '0', 'R'),
               ('q9', '1'): ('end', '1', 'R')}

q_accept = 'end'
blank_symbol = '#'


#%% Verstaile Shifts
def G(prev_sym, q, read_sym, move):
    """
    input: ... prev_sym q . read_sym .....
    """
    
    if (q, read_sym) not in transitions:
        raise ValueError(f"Transition for ({q}, {read_sym}) not found")

    q_next, write_sym, move = transitions[(q, read_sym)]

    if move == 'R':
        # write d' to current cell, move q' to the right (v1.v2 = d_{-1} d' · q')
        # return f"{prev_sym}{write_sym}.{q_next}"
        return [prev_sym, write_sym, '.', q_next]
    elif move == 'L':
        # move q' to the left (v1.v2 = q' d_{-1} · d')
        # return f"{q_next}{prev_sym}.{write_sym}"
        return [q_next, prev_sym, '.', write_sym]
    else:
        raise ValueError("Move must be 'L' or 'R'")

def F(q, d, transitions):
    """
    F: (q, d) → shift direction
    """
    if (q, d) not in transitions:
        raise ValueError(f"Transition for ({q}, {d}) not found")

    _, _, move = transitions[(q, d)]
    return -1 if move == 'R' else +1


#%%
# q, d = 'q0', '0'
# prev_sym = '#' 

# g_result = G(prev_sym, q, d, transitions)
# f_result = F(q, d, transitions)

# print(f"G({q}, {d}) = {g_result}")  # → #0.q1
# print(f"F({q}, {d}) = {f_result}")  # → +1

#%%
# def simulate_vs(tape, state, transitions, blank_symbol, max_steps=20, buff_len=100):
#     """
#     Simulate a Turing machine using Versatile Shift (VS) formalism.
#     The tape is centered with the read-write head at the middle dot position.
#     """
def read_DoD(s):
    # DoD: d_{-2}, d_{-1}, q, ·, d_0
    dot_pos = s.index('.')
    d_2 = s[dot_pos-2]
    d_1 = s[dot_pos-1]
    d0 = s[dot_pos+1]
    return d_2, d_1, d0

def replace_DoD_and_shift(s, g, f):
    dot_pos = s.index('.')
    
    s[dot_pos-2], s[dot_pos-1], s[dot_pos], s[dot_pos+1] = g    #update
    
    dot_pos = s.index('.')
    if f == 1:
        #dot to left
        temp = s[dot_pos-1]
        s[dot_pos-1] = '.'
        s[dot_pos] = temp
    elif f == -1:
        #dot to right
        temp = s[dot_pos+1]
        s[dot_pos+1] = '.'
        s[dot_pos] = temp
    else:
        raise SystemError
    
    return s
    

def show_dotted(s):
    print(''.join(s))

#%% sim
tape='00000011#00001000'
state='q0'
max_steps=500
buff_len=10

tape_buffer = [blank_symbol] * buff_len + [state, '.'] + list(tape) + [blank_symbol] * buff_len
s = deque(tape_buffer)


for step in range(max_steps):
    # DoD:  -2, -1, 0
    d_2, d_1, d0 = read_DoD(s)
    
    key = (d_1, d0)
    if key not in transitions:
        print(f"\n[STOP] No transition defined for ({d_1}, {d0})")
        break
    
    # F and G 
    q_next, write_sym, move = transitions[key]
    
    g = G(d_2, d_1, d0, move)
    f = F(d_1, d0, transitions)
    
    s = replace_DoD_and_shift(s, g, f)
    
    #halt
    _, q, _ = read_DoD(s)
    if q == q_accept:
        print("\n[HALT] sim success!")
        show_dotted(s)
        break
    
    







