#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 11 20:17:56 2025

@author: gelenag
"""
from collections import deque
from tqdm import tqdm

# %% Versatile Shifts
class TMVersatileShift:
    def __init__(self, states, symbols, transitions, accept_state, blank_symbol):
        self.states = states
        self.symbols = symbols
        self.transitions = transitions
        self.accept_state = accept_state
        self.blank_symbol = blank_symbol

        self.state_traj = []

    def simulate(self, initial_state, initial_tape, max_steps=500, buff_len=10, utm=False, utm_encoded_halting_state=None):
        self.tape_buffer = [self.blank_symbol] * buff_len + [initial_state,
                                                             '.'] + list(initial_tape) + [self.blank_symbol] * buff_len
        self.s = deque(self.tape_buffer)

        for step in tqdm(range(max_steps), total=max_steps):
            # DoD:  -2, -1, 0
            d_2, d_1, d0 = self.read_DoD()
            
            self.state_traj.append(d_1)
            
            key = (d_1, d0)
            if key not in self.transitions:
                print(f"\n[STOP] No transition defined for ({d_1}, {d0})")
                break

            # F and G
            q_next, write_sym, move = self.transitions[key]

            g = self.G(d_2, d_1, d0, move)
            f = self.F(d_1, d0)
            
            # if f == 0:
            #     pass
            
            self.replace_DoD_and_shift(g, f)

            # halt
            _, q, _ = self.read_DoD()
            self.show_dotted()
            if utm:
                # HALT for UTM
                # TODO: fix, maybe another neat solution
                if q == 'CP_CLN':
                    buff = ''.join(list(self.s)[self.s.index('X')+1:self.s.index('X')+31])
                    if buff.split('0')[0] == utm_encoded_halting_state:
                        print(f"[HALT] Accept state reached at step {step}")
                        # self.show_dotted()
                        break
                    
            else:
                # HALT for standart turing machines
                if q == self.accept_state:
                    print(f"[HALT] Accept state reached at step {step}")
                    self.show_dotted()
                    break

    def read_DoD(self):
        # DoD: d_{-2}, d_{-1}, q, ·, d_0
        dot_pos = self.s.index('.')
        d_2 = self.s[dot_pos-2]
        d_1 = self.s[dot_pos-1]
        d0 = self.s[dot_pos+1]
        return d_2, d_1, d0

    def replace_DoD_and_shift(self, g, f):
        dot_pos = self.s.index('.')

        self.s[dot_pos-2], self.s[dot_pos-1], self.s[dot_pos], self.s[dot_pos+1] = g  # update

        dot_pos = self.s.index('.')
        if f == 1:
            # dot to left
            temp = self.s[dot_pos-1]
            self.s[dot_pos-1] = '.'
            self.s[dot_pos] = temp
        elif f == -1:
            # dot to right
            temp = self.s[dot_pos+1]
            self.s[dot_pos+1] = '.'
            self.s[dot_pos] = temp
        elif f == 0:
            pass
        else:
            raise SystemError

    def show_dotted(self):
        print(''.join(self.s))

    def G(self, prev_sym, q, read_sym, move):
        """
        input: ... prev_sym q . read_sym .....
        """

        if (q, read_sym) not in self.transitions:
            raise ValueError(f"Transition for ({q}, {read_sym}) not found")

        q_next, write_sym, move = self.transitions[(q, read_sym)]

        if move == 'R':
            # write d' to current cell, move q' to the right (v1.v2 = d_{-1} d' · q')
            # return f"{prev_sym}{write_sym}.{q_next}"
            return [prev_sym, write_sym, '.', q_next]
        elif move == 'L':
            # move q' to the left (v1.v2 = q' d_{-1} · d')
            # return f"{q_next}{prev_sym}.{write_sym}"
            return [q_next, prev_sym, '.', write_sym]
        elif move == 'N':
            # no move
            return [prev_sym, q_next, '.', write_sym]
        else:
            raise ValueError("Move must be 'L' or 'R'")

    def F(self, q, d):
        """
        F: (q, d) → shift direction
        """
        if (q, d) not in self.transitions:
            raise ValueError(f"Transition for ({q}, {d}) not found")

        _, _, move = self.transitions[(q, d)]
        if move == 'R':
            return -1
        elif move == 'L':
            return 1
        elif move == 'N':
            return 0
        else:
            raise SystemError

