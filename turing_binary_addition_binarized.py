#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 11:26:15 2024

@author: gelenag

#trying to add 1101 + 101 = 10010: 13 + 5 = 18

"""

from pathlib import Path
from UNN.Turing import TuringMachineConfiguration, TuringMachine

def read_file(path):
    reading = Path(path).read_text()
    return reading

def load_turing_machine(machine_path):
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
    machine = TuringMachineConfiguration(states, symbols, None, transitions, '_', initial_state, accept_states, initial_tape)
        
    return machine

# tm = TuringMachine(states, alphabet, tape_alphabet, start_state, accept_states, verbose=True)
machine_config = load_turing_machine('TMs/binary_addition.txt')
binary_machine_config = machine_config.convert_to_binary()

new_tm = TuringMachine()
new_tm.load_configuration(binary_machine_config)
new_tm.run()

