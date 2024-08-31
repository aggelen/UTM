#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 11:22:10 2024

@author: gelenag
"""
import math
import numpy as np
from collections import deque
from pathlib import Path

def read_file(path):
    reading = Path(path).read_text()
    return reading

#%%
class TuringMachineConfiguration:
    def __init__(self, states, alphabet, tape_alphabet, transitions, blank_symbol, start_state, accept_states, initial_tape):
        self.states = states
        self.alphabet = alphabet
        if blank_symbol not in self.alphabet:
            self.alphabet = [blank_symbol] + self.alphabet
        self.tape_alphabet = tape_alphabet
        self.blank_symbol = blank_symbol
        self.start_state = start_state
        self.accept_states = accept_states
        self.transitions = {}
        
        for t in transitions:
            self.transitions[(t[0], t[1])] = t[2:]
        
        self.tape = initial_tape
        self.head_position = 0
    
    @staticmethod
    def _to_binary(number, bit_depth):
        """Convert a number to its binary representation with fixed bit depth"""
        binary = str(bin(number))[2:]
        while len(binary) < bit_depth:
            binary = "0" + binary
        return binary
    
    def convert_to_binary(self):
        """Convert the Turing machine to a binary Turing machine with only two symbols.
        This is done by encoding each symbol in binary using a fixed-width encoding.
        This is necessary as the resulting TM will not be able to distinguish between a meaningful blank
        and one of the infinite blanks at the start and end of the tape. So instead, each transition of
        the original TM will be converted to a set of transitions that reads and writes one
        fixed-length encoded block and then moves the head to the next or previous block."""
        # collect all symbols in the transitions (left and right side)
        alphabet = [symbol for _, symbol in self.transitions.keys()]
        alphabet += [symbol for _, symbol, _ in self.transitions.values()]
        alphabet = sorted(set(alphabet))
        alphabet.remove(self.blank_symbol)
        alphabet = [self.blank_symbol] + alphabet  # make sure that the blank has the index 0 (encoded as 000...0)

        if len(alphabet) == 2:
            print("Conversion to 2-symbol TM skipped: Was already 2-symbol")
            return

        symbol_to_idx_lookup = {symbol: i for i, symbol in enumerate(alphabet)}  # give each symbol a unique number
        alphabet_size = len(alphabet)
        bit_depth = int(math.ceil(math.log(alphabet_size)/math.log(2)))

        new_transitions = {}
        new_stop_states = []

        original_states = sorted(set(state for state, _ in self.transitions.keys()))  # list of states

        # for each source state of the original Turing machine (left side of the transition)
        for original_source_state in original_states:
            source_id = 0
            target_id = 1

            # the binary TM needs this many transitions to encode a single transition of the original TM
            binary_read_transition_count = 2 ** (bit_depth+1) - 2

            # encode reading operation
            for _ in range(binary_read_transition_count//2):  # divide by 2. We handle reading 0 and 1 in one iteration

                # generate two transitions for reading each bit of the current origin state

                binary_source_state = original_source_state + "_" + str(source_id)
                binary_target_state = original_source_state + "_" + str(target_id)
                new_transitions[(binary_source_state, "0")] = (binary_target_state, "0", "R")

                target_id += 1

                binary_source_state = original_source_state + "_" + str(source_id)
                binary_target_state = original_source_state + "_" + str(target_id)
                new_transitions[(binary_source_state, "1")] = (binary_target_state, "1", "R")

                target_id += 1
                source_id += 1

            # encode write, move and state change for each read result

            # for each symbol that exists on the left side of a transition
            for symbol_idx, symbol in enumerate(alphabet):
                transition_left_side = (original_source_state, symbol)
                if transition_left_side in self.transitions:

                    transition_right_side = self.transitions[transition_left_side]
                    original_target_state, original_target_symbol, direction = transition_right_side

                    # convert original TM symbol to binary
                    original_target_symbol_idx = symbol_to_idx_lookup[original_target_symbol]
                    original_target_symbol_idx_binary = self._to_binary(original_target_symbol_idx, bit_depth)

                    # after reading a binary encoded symbol, we need to backtrack to the beginning of the binary symbol
                    symbol_encoding = 2 ** bit_depth - 2 + symbol_idx + 1  # offset +1 from the initial state
                    source_id = symbol_encoding

                    # for each bit, move the head left without changing anything (backtrack after reading)
                    for _ in range(bit_depth):
                        binary_source_state = original_source_state + "_" + str(source_id)
                        binary_target_state = original_source_state + "_" + str(target_id)
                        new_transitions[(binary_source_state, "0")] = (binary_target_state, "0", "L")
                        new_transitions[(binary_source_state, "1")] = (binary_target_state, "1", "L")
                        source_id = target_id
                        target_id += 1

                    # write each bit of the target symbol (encode writing operation)
                    for i in range(bit_depth):
                        write_symbol = original_target_symbol_idx_binary[i]
                        binary_source_state = original_source_state + "_" + str(source_id)
                        binary_target_state = original_source_state + "_" + str(target_id)
                        new_transitions[(binary_source_state, "0")] = (binary_target_state, write_symbol, "R")
                        new_transitions[(binary_source_state, "1")] = (binary_target_state, write_symbol, "R")
                        source_id = target_id
                        target_id += 1

                    # for each bit, move the head left without changing anything (backtrack after writing)
                    for _ in range(bit_depth):
                        binary_source_state = original_source_state + "_" + str(source_id)
                        binary_target_state = original_source_state + "_" + str(target_id)
                        new_transitions[(binary_source_state, "0")] = (binary_target_state, "0", "L")
                        new_transitions[(binary_source_state, "1")] = (binary_target_state, "1", "L")
                        source_id = target_id
                        target_id += 1

                    # for each bit, move the head left or right without changing anything (encode head movement)
                    for _ in range(bit_depth-1):  # end one early to allow special transition of final state
                        binary_source_state = original_source_state + "_" + str(source_id)
                        binary_target_state = original_source_state + "_" + str(target_id)
                        new_transitions[(binary_source_state, "0")] = (binary_target_state, "0", direction)
                        new_transitions[(binary_source_state, "1")] = (binary_target_state, "1", direction)
                        source_id = target_id
                        target_id += 1

                    # move by the missing bit without changing anything (encode the state change)
                    binary_target_state = original_target_state + "_" + str(0)
                    if original_target_state in self.accept_states:
                        new_stop_states.append(binary_target_state)
                    binary_source_state = original_source_state + "_" + str(source_id)
                    new_transitions[(binary_source_state, "0")] = (binary_target_state, "0", direction)
                    new_transitions[(binary_source_state, "1")] = (binary_target_state, "1", direction)

        # encode the tape to binary
        new_tape = ""
        for symbol in self.tape:
            new_tape += self._to_binary(symbol_to_idx_lookup[symbol], bit_depth)
        new_tape = list(new_tape)
        head_position = self.head_position * bit_depth

        # overwrite members, the old definition will be lost
        self.has_been_binarized = True
        self.binarized_bit_depth = bit_depth
        self.binarized_symbol_lookup = alphabet
        self.pre_binarize_blank = self.blank_symbol

        self.transitions = new_transitions
        self.accept_states = new_stop_states
        self.head_position = head_position
        self.tape = new_tape
        self.blank_symbol = "0"
        self.start_state = self.start_state + "_" + str(0)
        self.current_state = self.start_state
    
        states = [state for state, _ in self.transitions.keys()]
        states += [state for state, _, _ in self.transitions.values()]
        states = sorted(set(states))
        
        self.states = states
    
        return self
    
    def decode_binarized_tape(self):
        """Decodes the binarized tape back to the original alphabet"""
        assert self.has_been_binarized

        output = []
        tape_string = "".join(self.tape)
        tape_index = self.head_position

        # fill the beginning and end of the tape with 0 to align the bit fields
        while tape_index % self.binarized_bit_depth != 0:
            tape_string = "0" + tape_string
            tape_index += 1
        while len(tape_string) % self.binarized_bit_depth != 0:
            tape_string += "0"

        # convert each bit field to its corresponding original TM symbol
        while len(tape_string) >= self.binarized_bit_depth:
            symbol = tape_string[0:self.binarized_bit_depth]
            tape_string = tape_string[self.binarized_bit_depth:]
            symbol_idx = int(symbol, 2)
            output.append(self.binarized_symbol_lookup[symbol_idx])
        return output
    
    # def convert_to_binary(self):
    #     """Convert the Turing machine to a binary Turing machine with only two symbols.
    #     This is done by encoding each symbol in binary using a fixed-width encoding.
    #     This is necessary as the resulting TM will not be able to distinguish between a meaningful blank
    #     and one of the infinite blanks at the start and end of the tape. So instead, each transition of
    #     the original TM will be converted to a set of transitions that reads and writes one
    #     fixed-length encoded block and then moves the head to the next or previous block."""
        
    #     # collect all symbols in the transitions (left and right side)
    #     if len(self.alphabet) == 2:
    #         print("Conversion to 2-symbol TM skipped: Was already 2-symbol")
    #         return

    #     symbol_to_idx_lookup = {symbol: i for i, symbol in enumerate(self.alphabet)}  # give each symbol a unique number
    #     alphabet_size = len(self.alphabet)
    #     bit_depth = int(math.ceil(math.log(alphabet_size)/math.log(2)))

    #     new_transitions = {}
    #     new_stop_states = []
    #     self.original_states = self.states
        
    #     new_states = []
        
    #     # for each source state of the original Turing machine (left side of the transition)
    #     for original_source_state in self.states:
    #         source_id = 0
    #         target_id = 1

    #         # the binary TM needs this many transitions to encode a single transition of the original TM
    #         binary_read_transition_count = 2 ** (bit_depth+1) - 2

    #         # encode reading operation
    #         for _ in range(binary_read_transition_count//2):  # divide by 2. We handle reading 0 and 1 in one iteration

    #             # generate two transitions for reading each bit of the current origin state

    #             binary_source_state = original_source_state + "_" + str(source_id)
    #             binary_target_state = original_source_state + "_" + str(target_id)
    #             new_transitions[(binary_source_state, "0")] = (binary_target_state, "0", "R")
    #             new_states.append(binary_source_state)
    #             new_states.append(binary_target_state)
    #             target_id += 1

    #             binary_source_state = original_source_state + "_" + str(source_id)
    #             binary_target_state = original_source_state + "_" + str(target_id)
    #             new_transitions[(binary_source_state, "1")] = (binary_target_state, "1", "R")
    #             new_states.append(binary_source_state)
    #             new_states.append(binary_target_state)
    #             target_id += 1
    #             source_id += 1

    #         # encode write, move and state change for each read result

    #         # for each symbol that exists on the left side of a transition
    #         for symbol_idx, symbol in enumerate(self.alphabet):
    #             transition_left_side = (original_source_state, symbol)
    #             if transition_left_side in self.transitions:

    #                 transition_right_side = self.transitions[transition_left_side]
    #                 original_target_state, original_target_symbol, direction = transition_right_side

    #                 # convert original TM symbol to binary
    #                 original_target_symbol_idx = symbol_to_idx_lookup[original_target_symbol]
    #                 original_target_symbol_idx_binary = self._to_binary(original_target_symbol_idx, bit_depth)

    #                 # after reading a binary encoded symbol, we need to backtrack to the beginning of the binary symbol
    #                 symbol_encoding = 2 ** bit_depth - 2 + symbol_idx + 1  # offset +1 from the initial state
    #                 source_id = symbol_encoding

    #                 # for each bit, move the head left without changing anything (backtrack after reading)
    #                 for _ in range(bit_depth):
    #                     binary_source_state = original_source_state + "_" + str(source_id)
    #                     binary_target_state = original_source_state + "_" + str(target_id)
    #                     new_transitions[(binary_source_state, "0")] = (binary_target_state, "0", "L")
    #                     new_transitions[(binary_source_state, "1")] = (binary_target_state, "1", "L")
    #                     source_id = target_id
    #                     target_id += 1

    #                 # write each bit of the target symbol (encode writing operation)
    #                 for i in range(bit_depth):
    #                     write_symbol = original_target_symbol_idx_binary[i]
    #                     binary_source_state = original_source_state + "_" + str(source_id)
    #                     binary_target_state = original_source_state + "_" + str(target_id)
    #                     new_transitions[(binary_source_state, "0")] = (binary_target_state, write_symbol, "R")
    #                     new_transitions[(binary_source_state, "1")] = (binary_target_state, write_symbol, "R")
    #                     source_id = target_id
    #                     target_id += 1

    #                 # for each bit, move the head left without changing anything (backtrack after writing)
    #                 for _ in range(bit_depth):
    #                     binary_source_state = original_source_state + "_" + str(source_id)
    #                     binary_target_state = original_source_state + "_" + str(target_id)
    #                     new_transitions[(binary_source_state, "0")] = (binary_target_state, "0", "L")
    #                     new_transitions[(binary_source_state, "1")] = (binary_target_state, "1", "L")
    #                     source_id = target_id
    #                     target_id += 1

    #                 # for each bit, move the head left or right without changing anything (encode head movement)
    #                 for _ in range(bit_depth-1):  # end one early to allow special transition of final state
    #                     binary_source_state = original_source_state + "_" + str(source_id)
    #                     binary_target_state = original_source_state + "_" + str(target_id)
    #                     new_transitions[(binary_source_state, "0")] = (binary_target_state, "0", direction)
    #                     new_transitions[(binary_source_state, "1")] = (binary_target_state, "1", direction)
    #                     source_id = target_id
    #                     target_id += 1

    #                 # move by the missing bit without changing anything (encode the state change)
    #                 binary_target_state = original_target_state + "_" + str(0)
    #                 if original_target_state in self.accept_states:
    #                     new_stop_states.append(binary_target_state)
    #                 binary_source_state = original_source_state + "_" + str(source_id)
    #                 new_transitions[(binary_source_state, "0")] = (binary_target_state, "0", direction)
    #                 new_transitions[(binary_source_state, "1")] = (binary_target_state, "1", direction)

    #     # encode the tape to binary
    #     new_tape = ""
    #     for symbol in self.tape:
    #         new_tape += self._to_binary(symbol_to_idx_lookup[symbol], bit_depth)
    #     new_tape = list(new_tape)
    #     head_position = self.head_position * bit_depth

    #     # overwrite members, the old definition will be lost
    #     self.has_been_binarized = True
    #     self.binarized_bit_depth = bit_depth
    #     self.binarized_symbol_lookup = self.alphabet
    #     self.pre_binarize_blank = self.blank_symbol

    #     self.transitions = new_transitions
    #     self.accept_states = new_stop_states
    #     self.head_position = head_position
    #     self.tape = new_tape
    
    #     self.blank_symbol = "0"
    #     self.start_state = self.start_state + "_" + str(0)
        
    #     # self.states = sorted(list(set(new_states)))
    #     self.alphabet = ["0", "1"]
    #     return self
        
class TuringMachine:
    def __init__(self, states=None, alphabet=None, tape_alphabet=None, start_state=None, accept_states=None, blank_symbol='_', verbose=False):
        self.states = list(states) if states is not None else None
        self.alphabet = list(alphabet) if alphabet is not None else None
        
        if self.alphabet is not None:
            if blank_symbol not in self.alphabet:
                self.alphabet = self.alphabet + [blank_symbol]
                
        self.tape_alphabet = tape_alphabet
        self.blank_symbol = blank_symbol
        self.start_state = start_state
        self.accept_states = accept_states
        
        if self.states is not None and self.alphabet is not None:
            self.state_index = {state: i for i, state in enumerate(self.states)}
            self.symbol_index = {symbol: i for i, symbol in enumerate(self.alphabet)}
        
        self.machine_has_program = False
        self.machine_from_config = False
        self.machine_binarized = False
        
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
    
    def load_configuration(self, config):
       self.config = config
       self.states = config.states
       self.alphabet = config.alphabet
       if config.blank_symbol not in self.alphabet:
           self.alphabet = [config.blank_symbol] + self.alphabet
       self.tape_alphabet = self.alphabet
       self.blank_symbol = config.blank_symbol
       self.start_state = config.start_state
       self.accept_states = config.accept_states
       self.transitions = {}
       
       for t in config.transitions:
           self.transitions[(t[0], t[1])] = t[2:]
       
       self.tape = config.tape
       self.head_position = 0
       
       self.machine_has_program = True
       self.machine_from_config = True
       
       if config.has_been_binarized:
           self.machine_binarized = True
       
       self.state_index = {state: i for i, state in enumerate(self.states)}
       self.symbol_index = {symbol: i for i, symbol in enumerate(self.alphabet)}
       
       self.transition_table = np.full((len(self.states), len(self.alphabet)), None, dtype=object)
       for k, v in config.transitions.items():
            (s_pre, read), (s_post, write, direction) = k, v
            self.transition_table[self.state_index[s_pre], self.symbol_index[read]] = (s_post, write, direction)
       self.machine_has_program = True
       self.reset("".join(self.tape))
       
    
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

    def run(self, input_string=None):
        if self.machine_has_program:
            
            if not self.machine_from_config:
                self.reset(input_string)
            
            while self.current_state not in self.accept_states:
                if self.verbose:
                    self.print_tape()
                    
                if not self.step():
                    break
            
            if self.current_state in self.accept_states:
                print("-------- Halt! --------")
                print("-------- Decoded Tape! --------")
                if self.machine_binarized:
                    decoded = self.config.decode_binarized_tape()
                    print(''.join(decoded).replace('_',''))
                else:
                    self.print_tape()
                return True
            else:
                return False
        
        else:
            raise Exception("The Turing machine cannot create state transitions. You had to load a program. Please use .load_program() method.")
            
            
#%% Minsky's Small Universal Turing Machine 4 symbols, 7 states
class Minsky47UniversalTuringMachine(TuringMachine):
    def __init__(self):
        
        super().__init__(states=['Q0', 'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6'],
                         alphabet=['0', '1', '2', '3'], 
                         tape_alphabet=['0', '1', 'b', 'c'], 
                         start_state='Q1', 
                         accept_states='Q1', 
                         blank_symbol='0')
        
        N1 = 1
        # Nk+1 = Nk + mk + 1 
        
        self.load_program('TMs/Minsky4Sym7St.txt')
        
    def load_two_tag_system(self, system):
        pass
    
    def run(self, input_string):
        pass
    