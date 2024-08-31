#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 24 13:59:34 2024

@author: gelenag
"""
import re
from pathlib import Path
from UNN.Turing import TuringMachineConfiguration

def read_file(path):
    reading = Path(path).read_text()
    return reading

class System:
    def __init__(self, alphabet=None, production=None, verbose=False):
        self.verbose = verbose            
        self.alphabet = alphabet
        self.production = production
        
        if production is not None:
            self.parse_production()
        
    def parse_production(self):
        self.production_lhs = []
        self.production_rhs = [] 
        
        for p in self.production:
            lhs, rhs = p.split(' -> ')
            self.production_lhs.append(lhs)
            self.production_rhs.append(rhs)
            
    def forward(self, input_string):
        pass

        
class PostCanonicalSystem(System):
    def __init__(self, alphabet, production):
        super().__init__(alphabet, production)

    def generate_variables_and_regex_pattern(self, production_lhs):
        pattern = r'\(\$\d+\)'
        variables = re.findall(pattern, production_lhs)
        
        regex_pattern = (production_lhs + '.')[:-1]    # to copy!
        for v in variables:
            regex_pattern = regex_pattern.replace(v, '(.*)')
        
        return variables, regex_pattern
    
    def generate_output(self, values, production_rhs):
        op = (production_rhs + '.')[:-1]    # to copy!
        for k, v in values.items():
            op = op.replace(k, v)
        return op
            
    
    def match_variables_to_values(self, input_string, production_lhs):
        variables, regex_pattern = self.generate_variables_and_regex_pattern(production_lhs)
        
        match = re.match(regex_pattern, input_string)
        
        values = {}
        
        if match:
            for i, v in enumerate(variables):
                values[v] = match.group(1+i)
        return values

    def forward(self, input_string):
        output = (input_string+'.')[:-1]
        for i in range(len(self.production_lhs)):
            values = self.match_variables_to_values(output, self.production_lhs[i])
            output = self.generate_output(values, self.production_rhs[i])
        return output


class TwoTagSystem(System):
    def __init__(self, alphabet=None, production=None, verbose=False):
        super().__init__(alphabet, production, verbose)
        self.steps = 0
        
    def parse_string(self, input_string):
        pattern = '|'.join(re.escape(tag) for tag in self.alphabet)
        matches = re.findall(pattern, input_string)
        
        if '->' in input_string:
            before_arrow, after_arrow = input_string.split('->')
            before_parts = [match for match in re.findall(pattern, before_arrow)]
            after_parts = [match for match in re.findall(pattern, after_arrow)]
            return before_parts, after_parts
        else:
            return matches
        
    def parse_production(self):
        self.parsed_production = []
        self.halt_prod_symbol = None
        for i, p in enumerate(self.production):
            m = self.parse_string(p)
            self.parsed_production.append(m)
            if '*' in m[1]:
                self.halt_prod_symbol = m[0][0]
            
    def apply_2_tag(self, parsed_input):
        # prod_id = self.alphabet.index(parsed_input[0])
        for i, c in enumerate(self.parsed_production):
            if c[0][0] == parsed_input[0]:
                current_prod = c
                continue
        
   
        halt = False
        
        # remove first two
        parsed_input.pop(0)
        parsed_input.pop(0)
        # apply production by prod_id
        tobe_append = [i for i in current_prod[1]]
        if "_" in tobe_append:
            tobe_append.remove("_")
        parsed_input += tobe_append
       
        op = parsed_input
        
        if op[0] == self.halt_prod_symbol or len(op) < 2:
            halt = True
        
        return halt, op
        
        
    def forward(self, input_string):
        parsed_input = self.parse_string(input_string)
        halt = False
        while not halt:
            if self.verbose:
                printstr = ''.join(parsed_input) + " -> "
            halt, parsed_input = self.apply_2_tag(parsed_input)
            if self.verbose:
                printstr += ''.join(parsed_input)
            print(printstr)
        
        return ''.join(parsed_input)


    def load_turing_machine(self, machine_path):
        definition = read_file(machine_path)
        transitions = []
        lines = definition.splitlines()
        for ln_id, ln in enumerate(lines):
            if '#states:' in ln:
                states = ln.split(" ")[1:]
            if '#symbols:' in ln:
                symbols = ln.split(" ")[1:]
            if '#initial_state:' in ln:
                initial_state = ln.split(" ")[1] 
            if "#accept_states:" in ln:
                accept_states = ln.split(" ")[1:] 
            if "#initial_tape:" in ln:
                initial_tape = ln.split(" ")[1] 
                
            if '#transition_table' in ln:
                for i in range(ln_id+1, len(lines)):
                    transitions.append(lines[i].strip().split(" "))
                break
        
        # tm config : states, alphabet, tape_alphabet, transitions, blank_symbol, start_state, accept_states
        self.machine = TuringMachineConfiguration(states, symbols, None, transitions, '_', initial_state, accept_states, initial_tape)
            
        return self.machine
    
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
        assert tm_direction in ("L", "R")  # only left and right head movement is supported

        # set up the production rules for right and left head movement according to the Cocke and Minsky paper
        # refer to the paper in the "literature" directory for details
        # The strings "$", "!0" and "!1" are placeholders and will be replaced by
        # the corresponding adapted Turing machine state names.
        if tm_direction == "R":
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
        elif tm_direction == "L":
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
    
    def from_turing_machine(self, machine_path):
        machine = self.load_turing_machine(machine_path).convert_to_binary()
    
        #%% Convert formalism
        new_transitions = []
        
        for k, v in machine.transitions.items():
            (source_state, read_symbol), (target_state, write_symbol, direction) = k, v
            new_state = source_state + "_" + read_symbol

            # the tm-like construct will have separate states for having read a 0 or a 1
            if target_state in machine.accept_states:
                qi_0 = target_state
                qi_1 = target_state
            else:
                qi_0 = target_state + "_0"
                qi_1 = target_state + "_1"

            new_transition = (new_state, write_symbol, direction, qi_0, qi_1)
            new_transitions.append(new_transition)
            
        machine.transitions_in_second_formalism = new_transitions
        
        # Express the tm tape (which only has 0s and 1s) as two binary numbers, m and n (left and right of the head)
        tape_m = 0
        tape_n = 0
        for i, symbol in enumerate(machine.tape):
            tape_n += int(symbol) * 2 ** i

        # A special unique start state (uss) needs to be prepended since the Turing machine's original start state
        # was split into two states and we must begin with a single start state
        uss = "q_init_0"

        uss_transition = (uss, "0", "R", machine.start_state + "_0", machine.start_state + "_1")
        new_transitions.append(uss_transition)

        # Convert the start tape's two binary numbers into a two tag system's start word of the form
        # [A x a x a x... a x B x b x b x...b x] where each a x and b x occurs m and n times, respectively.
        # The upper case A x and B x only occur once and act as separators between the left and right hand side
        # Each adapted state 's' will receive their own A and B variants, named a_'s' and b_'s'.
        # In this instance, 's' is the unique start state uss. The remaining a_'s' and b_'s' will be defined later.
        start_word = ["A_" + uss, "x"] + ["a_" + uss, "x"] * tape_m + ["B_" + uss, "x"] + ["b_" + uss, "x"] * tape_n

        production_rules = {}

        # convert the tm's adapted transitions to two tag system production rules
        for adapted_transition in new_transitions:
            prod_rules = self.transition_to_production_rules(adapted_transition, machine.accept_states)

            # add the production rules for a single transition to the dictionary of all production rules
            for key, value in prod_rules.items():
                assert key not in production_rules
                production_rules[key] = value

        self.production_rules = production_rules
        self.current_word = start_word
        self.halting_symbol = "#"
        self.steps = 0
        
        self.get_word_as_tm_tape()
        
        return self
    
    def get_word_as_tm_tape(self):
        """Return the two tag system's current word in the form of the original binary TM's tape"""

        assert self.current_word[0] == "#" or self.current_word[0].startswith("A")
        assert self.current_word[1] == "x"

        # the word should now look like this:
        # - a single "A x"
        # - one or more "a x"
        # - a single "B x"
        # - one or more "b x"
        # A x and B x act as separators

        word = self.current_word[2:]  # cut off the initial "A x"
        m = 0
        n = 0

        # count all "a x" until "B x" is reached
        while not word[0].startswith("B"):
            assert word[0].startswith("a") and word[1] == "x"
            m += 1
            assert len(word) % 2 == 0
            word = word[2:]

        assert word[0].startswith("B") and word[1] == "x"
        word = word[2:]  # cut off the "B x"

        # count all "b x" until the end
        while word:
            assert word[0].startswith("b") and word[1] == "x"
            n += 1
            assert len(word) % 2 == 0
            word = word[2:]

        # convert numbers to binary strings, with the right string reversed
        left = bin(m)[2:] if m > 0 else ""
        right = bin(n)[2:] if n > 0 else ""
        right = "".join((reversed(right)))
        return left + "^" + right  # mark the head position with a ^
    
    def step(self):
        first_symbol = self.current_word[0]
        self.current_word = self.current_word[2:] + self.production_rules[first_symbol]
        self.steps += 1
        
    def run(self):   
        print("Initial Tape:")
        decoded_tape = self.get_word_as_tm_tape()
        self.machine.head_position = decoded_tape.index('^')
        self.machine.tape = list(decoded_tape.replace('^', ''))
        decoded_output = self.machine.decode_binarized_tape()
        print(''.join(decoded_output).replace('_',''))
        
        # print(decoded_tape)
        while self.current_word[0] != self.halting_symbol and len(self.current_word) >= 2:
            self.step()

            
        print("Final Result:")
        
        decoded_tape = self.get_word_as_tm_tape()
        # print(decoded_tape)
        
        self.machine.head_position = decoded_tape.index('^')
        self.machine.tape = list(decoded_tape.replace('^', ''))
        decoded_output = self.machine.decode_binarized_tape()
        print(''.join(decoded_output).replace('_',''))
        
