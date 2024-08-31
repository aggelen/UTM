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
        
        self.initial_tape = initial_tape
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
        if len(self.alphabet) == 2:
            print("Conversion to 2-symbol TM skipped: Was already 2-symbol")
            return

        symbol_to_idx_lookup = {symbol: i for i, symbol in enumerate(self.alphabet)}  # give each symbol a unique number
        alphabet_size = len(self.alphabet)
        bit_depth = int(math.ceil(math.log(alphabet_size)/math.log(2)))

        new_transitions = {}
        new_stop_states = []
        self.original_states = self.states
        
        new_states = []
        
        # for each source state of the original Turing machine (left side of the transition)
        for original_source_state in self.states:
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
                new_states.append(binary_source_state)
                new_states.append(binary_target_state)
                target_id += 1

                binary_source_state = original_source_state + "_" + str(source_id)
                binary_target_state = original_source_state + "_" + str(target_id)
                new_transitions[(binary_source_state, "1")] = (binary_target_state, "1", "R")
                new_states.append(binary_source_state)
                new_states.append(binary_target_state)
                target_id += 1
                source_id += 1

            # encode write, move and state change for each read result

            # for each symbol that exists on the left side of a transition
            for symbol_idx, symbol in enumerate(self.alphabet):
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
        for symbol in self.initial_tape:
            new_tape += self._to_binary(symbol_to_idx_lookup[symbol], bit_depth)
        new_tape = list(new_tape)
        head_position = self.head_position * bit_depth

        # overwrite members, the old definition will be lost
        self.has_been_binarized = True
        self.binarized_bit_depth = bit_depth
        self.binarized_symbol_lookup = self.alphabet
        self.pre_binarize_blank = self.blank_symbol

        self.transitions = new_transitions
        self.accept_states = new_stop_states
        self.head_position = head_position
        self.tape = new_tape
        self.blank_symbol = "0"
        self.start_state = self.start_state + "_" + str(0)
        
        self.states = sorted(list(set(new_states)))
        self.alphabet = ["0", "1"]
        return self
        
class TuringMachine:
    def __init__(self, states, alphabet, tape_alphabet, start_state, accept_states, blank_symbol='_', verbose=False):
        self.states = list(states)
        self.alphabet = list(alphabet)
        if blank_symbol not in self.alphabet:
            self.alphabet = self.alphabet + [blank_symbol]
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
    
    def run(self, input_string):
        pass
    
    
#%%
class TwoTagSystem:
    def __init__(self):
        self.production_rules = None
        self.current_word = [""]
        self.halting_symbol = ""
        self.steps = 0
    
    def load_tm(self, tm_path):
        # definition = read_file(tm_path)
        # transitions = []
        # lines = definition.splitlines()
        # for ln_id, ln in enumerate(lines):
        #     if 'states:' in ln:
        #         states = ln.split(" ")[1:]
        #     if 'symbols:' in ln:
        #         symbols = ln.split(" ")[1:]
        #     if 'initial_state:' in ln:
        #         initial_state = ln.split(" ")[1] 
        #     if "accept_states:" in ln:
        #         accept_states = ln.split(" ")[1:] 
        #     if "initial_tape:" in ln:
        #         initial_tape = ln.split(" ")[1] 
                
        #     if 'transition_table' in ln:
        #         for i in range(ln_id+1, len(lines)):
        #             transitions.append(lines[i].strip().split(" "))
        #         break
        # return states, symbols, initial_state, accept_states, initial_tape, transitions
        
        transitions = {
            ("q0", "1"): ("q0", "1", ">"),
            ("q0", "0"): ("q1", "0", ">"),
            ("q1", "0"): ("qend", "0", "<"),
            ("q1", "1"): ("q2", "0", "<"),
            ("q2", "0"): ("q3", "1", ">"),
            ("q3", "0"): ("q1", "0", ">"),
        }

        return ['q0', 'q1', 'q2', 'q3', 'q_end'], ['0', '1'], 'q0', ["qend"],"111011", transitions
                
    @staticmethod
    def transition_to_production_rules(adapted_transition, tm_stop_states):
        """Convert a single adapted Turing machine transition into
        a set of multiple two tag system production rules
        Arguments:
            adapted_transition: The transition to be converted (5-tuple, see function convert_tm_to_two_tag_system())
            tm_stop_states:     The Turing machine's stop states (list)"""

        tm_state, tm_write_symbol, tm_direction, tm_state_change_0, tm_state_change_1 = adapted_transition

        # rename the stop states to the stopping symbol "#"
        if tm_state_change_0 in tm_stop_states:
            tm_state_change_0 = "#"
        if tm_state_change_1 in tm_stop_states:
            tm_state_change_1 = "#"

        assert tm_write_symbol in ("0", "1")  # make sure the Turing machine is actually binary
        assert tm_direction in ("<", ">")  # only left and right head movement is supported

        # set up the production rules for right and left head movement according to the Cocke and Minsky paper
        # refer to the paper in the "literature" directory for details
        # The strings "$", "!0" and "!1" are placeholders and will be replaced by
        # the corresponding adapted Turing machine state names.
        if tm_direction == ">":
            production_rules = {
                "A$": ["C$", "x"] if tm_write_symbol == "0" else ["C$", "x", "c$", "x"],
                "a$": ["c$", "x", "c$", "x"],
                "B$": ["S$"],
                "b$": ["s$"],
                "C$": ["D$_1", "D$_0"],
                "c$": ["d$_1", "d$_0"],
                "S$": ["T$_1", "T$_0"],
                "s$": ["t$_1", "t$_0"],
                "D$_1": ["A!1", "x"],
                "d$_1": ["a!1", "x"],
                "T$_1": ["B!1", "x"],
                "t$_1": ["b!1", "x"],
                "D$_0": ["x", "A!0", "x"],
                "d$_0": ["a!0", "x"],
                "T$_0": ["B!0", "x"],
                "t$_0": ["b!0", "x"],
            }
        elif tm_direction == "<":
            production_rules = {
                # switch A and B (is now called Z)
                "A$": ["Z$", "x"],
                "a$": ["z$", "x"],
                # Z (formerly A) now takes the role of B
                "Z$": ["S$"],
                "z$": ["s$"],
                # B takes the role of (formerly) A
                "B$": ["C$", "x"] if tm_write_symbol == "0" else ["C$", "x", "c$", "x"],
                "b$": ["c$", "x", "c$", "x"],
                "C$": ["D$_1", "D$_0"],
                "c$": ["d$_1", "d$_0"],
                "S$": ["T$_1", "T$_0"],
                "s$": ["t$_1", "t$_0"],

                "D$_1": ["Y$_1", "x"],
                "d$_1": ["y$_1", "x"],
                "T$_1": ["A!1", "x"],
                "t$_1": ["a!1", "x"],
                "D$_0": ["x", "Y$_0", "x"],
                "d$_0": ["y$_0", "x"],
                "T$_0": ["A!0", "x"],
                "t$_0": ["a!0", "x"],

                "Y$_0": ["B!0", "x"],
                "y$_0": ["b!0", "x"],
                "Y$_1": ["B!1", "x"],
                "y$_1": ["b!1", "x"]
            }
        else:
            assert False

        # iterate over the production rules and make some final adaptations
        final_production_rules = {}
        for source_symbol, target_symbols in production_rules.items():
            source_symbol = source_symbol.replace("$", "_" + str(tm_state))  # replace placeholder by tm state names

            # iterate over the targets (right-hand side) of the production rules and make some final adaptations
            final_targets = []
            for target in target_symbols:
                # set the halting symbol to the target to make the two tag system stop
                if (target == "A!0" and tm_state_change_0 == "#") or (target == "A!1" and tm_state_change_1 == "#"):
                    target = "#"
                else:  # if not stopping, replace placeholders by tm state names
                    target = target.replace("$", "_" + str(tm_state))
                    target = target.replace("!0", "_" + str(tm_state_change_0))
                    target = target.replace("!1", "_" + str(tm_state_change_1))
                final_targets.append(target)
            final_production_rules[source_symbol] = final_targets

        return final_production_rules
    
    def from_turing_machine(self, tm_path):
        """Convert a binary Turing machine to a two tag system.
        For details refer to the Cocke/Minsky paper in the 'literature' directory.
        From: https://github.com/Cerno-b/mtg-turing-machine"""
        
        states, symbols, initial_state, accept_states, initial_tape, transitions = self.load_tm(tm_path)
        
        adapted_transitions = []  # list of transitions adapted to the tm-like construct

        for k,v in transitions.items():
            (source_state, read_symbol), (target_state, write_symbol, direction) = k, v
            adapted_state = source_state + "_" + read_symbol

            # the tm-like construct will have separate states for having read a 0 or a 1
            if target_state in accept_states:
                adapted_state_change_0 = target_state
                adapted_state_change_1 = target_state
            else:
                adapted_state_change_0 = target_state + "_0"
                adapted_state_change_1 = target_state + "_1"

            adapted_transition = (adapted_state, write_symbol, direction,
                                  adapted_state_change_0, adapted_state_change_1)
            adapted_transitions.append(adapted_transition)

        # Express the tm tape (which only has 0s and 1s) as two binary numbers, m and n (left and right of the head)
        tape_m = 0
        tape_n = 0
        for i, symbol in enumerate(initial_tape):
            tape_n += int(symbol) * 2 ** i

        # A special unique start state (uss) needs to be prepended since the Turing machine's original start state
        # was split into two states and we must begin with a single start state
        uss = "q_init_0"

        uss_transition = (uss, "0", ">", initial_state + "_0", initial_state + "_1")
        adapted_transitions.append(uss_transition)

        # Convert the start tape's two binary numbers into a two tag system's start word of the form
        # [A x a x a x... a x B x b x b x...b x] where each a x and b x occurs m and n times, respectively.
        # The upper case A x and B x only occur once and act as separators between the left and right hand side
        # Each adapted state 's' will receive their own A and B variants, named a_'s' and b_'s'.
        # In this instance, 's' is the unique start state uss. The remaining a_'s' and b_'s' will be defined later.
        start_word = ["A_" + uss, "x"] + ["a_" + uss, "x"] * tape_m + ["B_" + uss, "x"] + ["b_" + uss, "x"] * tape_n

        production_rules = {}

        # convert the tm's adapted transitions to two tag system production rules
        for adapted_transition in adapted_transitions:
            prod_rules = self.transition_to_production_rules(adapted_transition, accept_states)

            # add the production rules for a single transition to the dictionary of all production rules
            for key, value in prod_rules.items():
                assert key not in production_rules
                production_rules[key] = value

        self.production_rules = production_rules
        self.current_word = start_word
        self.halting_symbol = "#"
        self.steps = 0
        return self
    
    def print(self):
        """Print the current state of the two tag system"""
        first_symbol = self.current_word[0]
        if first_symbol == self.halting_symbol:
            print("\rstep:", self.steps, "- word:", self.get_brief_word())
            print("Halting Symbol reached.")
        else:
            print("\rstep:", self.steps,
                  "- rule:", first_symbol, "->", self.production_rules[first_symbol],
                  "- word:", self.get_brief_word())
    
    def get_brief_word(self):
      """The two tag system's word will get very long if the tts was derived from a Turing machine.
      Instead of outputting all 'a x' and 'b x' repetitions, repeated occurrences of symbol pairs will be
      represented by the pair, followed by its count, e.g. '[a x]^5' for 5 occurrences of the 'a x' pair."""
      word_copy = self.current_word
      current_symbol_pair = []
      count = 0

      brief_word = ""
      while len(word_copy) >= 2:

          # cut off a symbol pair
          symbol_pair = word_copy[0:2]
          word_copy = word_copy[2:]

          if current_symbol_pair == symbol_pair:  # if it fits the currently counted pair, increment
              count += 1
          else:  # otherwise switch to the new pair and append the old one to the brief word
              if current_symbol_pair:
                  brief_word += "({symbol})^{count}, ".format(count=count, symbol=" ".join(current_symbol_pair))
              current_symbol_pair = symbol_pair
              count = 1
      brief_word += "({symbol})^{count}, ".format(count=count, symbol=" ".join(current_symbol_pair))

      # if a single symbol is left (odd number of symbols in the word), append it
      if len(word_copy) > 0:
          brief_word += "({symbol})^1, ".format(symbol=" ".join(word_copy))
      return brief_word
      
    def step(self):
        """Compute a single step of the two tag system"""
        # cut off the first two symbols and place the result of the production rule based on the first symbol to the
        # end of the word
        first_symbol = self.current_word[0]
        self.current_word = self.current_word[2:] + self.production_rules[first_symbol]
        self.steps += 1      
  
    def run(self, silent=False, brief=True):
        first_symbol = self.current_word[0]
        if not silent:
            if brief:
                print("Number of transitions:", len(self.production_rules))
                print("Initial state:", self.get_brief_word())
            else:
                self.print_definition()
                print(first_symbol, "->", self.production_rules[first_symbol])
        # repeat until halting symbol reached or current word becomes shorter than 2 symbols
        while self.current_word[0] != self.halting_symbol and len(self.current_word) >= 2:
            self.step()
            first_symbol = self.current_word[0]
            if not silent:
                # in case of a tts based on a tm, only give status updates after one tts cycle ends
                if brief and self.from_turing_machine:
                    if first_symbol.startswith("A"):
                        self.print()
                else:  # in all other cases (brief == False or tts not based on tm), always give status updates
                    self.print()

        # in case of tts based on a tm, convert the final word back to a tm tape
        # if self.from_turing_machine:
        #     print()
        #     print("Final Result:")
        #     print(self.get_word_as_tm_tape())

    
    