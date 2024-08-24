#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 11:22:10 2024

@author: gelenag
"""

import numpy as np
from collections import deque
from pathlib import Path

def read_file(path):
    reading = Path(path).read_text()
    return reading

class TuringMachine:
    def __init__(self, states, alphabet, tape_alphabet, start_state, accept_states, blank_symbol='_', verbose=False):
        self.states = list(states)
        self.alphabet = list(alphabet) + [blank_symbol]
        self.tape_alphabet = tape_alphabet
        self.blank_symbol = blank_symbol
        self.start_state = start_state
        self.accept_states = accept_states
        self.state_index = {state: i for i, state in enumerate(self.states)}
        self.symbol_index = {symbol: i for i, symbol in enumerate(self.alphabet)}
        
        self.machine_has_program = False
        
        # Use deque for the tape to allow easy expansion in both directions
        self.tape = deque()
        self.head_position = 0
        self.current_state = start_state
        
        self.verbose = verbose
    
    def load_program(self, program_path):
        program = read_file(program_path)
        self.transition_table = np.full((len(self.states), len(self.alphabet)), None, dtype=object)
        for line in program.splitlines():
            if len(line):
                s_pre, read, s_post, write, direction = line.split(' ')
                self.transition_table[self.state_index[s_pre], self.symbol_index[read]] = (s_post, write, direction)
        self.machine_has_program = True
        self.reset('')
    
    def reset(self, input_string):
        self.tape.clear()
        self.tape.extend([self.blank_symbol] * 100)  # Initialize with some blanks to simulate infinite tape
        self.head_position = len(self.tape) // 2
        self.current_state = self.start_state
        for i, char in enumerate(input_string):
            self.tape[self.head_position + i] = char
    
    def step(self):
        if not self.machine_has_program:
            raise Exception("No program loaded")
        
        current_symbol = self.tape[self.head_position]
        state_idx = self.state_index[self.current_state]
        symbol_idx = self.symbol_index[current_symbol]
        
        transition = self.transition_table[state_idx, symbol_idx]
        if transition is None:
            print("-------- Rejected --------")
            return False  # Halts if no valid transition

        next_state, write_symbol, move_direction = transition
        
        self.tape[self.head_position] = write_symbol
        if move_direction == 'R':
            self.head_position += 1
            if self.head_position >= len(self.tape):
                self.tape.append(self.blank_symbol)
        else:  # 'L'
            if self.head_position <= 0:
                self.tape.appendleft(self.blank_symbol)
                self.head_position += 1
            self.head_position -= 1
        
        self.current_state = next_state
        return True

    def print_tape(self):
        tape_str = ''.join(self.tape).strip(self.blank_symbol)
        print(f"{tape_str} {self.current_state}")

    def run(self, input_string):
        if self.machine_has_program:
            self.reset(input_string)
            
            while self.current_state not in self.accept_states:
                if self.verbose:
                    self.print_tape()
                    
                if not self.step():
                    break
            
            if self.current_state in self.accept_states:
                print("-------- Halt! --------")
                self.print_tape()
                return True
            else:
                return False
        
        else:
            raise Exception("The Turing machine cannot create state transitions. You had to load a program. Please use .load_program() method.")