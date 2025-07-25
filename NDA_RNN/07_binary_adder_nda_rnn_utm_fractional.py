#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 26 12:54:07 2025

@author: gelenag
"""

from NeuralUTM.SymbolicDynamics import TMVersatileShift
from NeuralUTM.Encoders import GodelEncoder, MPFGodelEncoder, RationalGodelEncoder
from NeuralUTM.Automata import TMNonlinearDynamicalAutomaton, create_transition_animation
from NeuralUTM.NN import FastNDAtoRANN

from NeuralUTM.Helpers import read_turing_machine_from_txt, BinaryTMEncoder, TMDescriptor

#%%
# import json

# with open("UTM_traj.json", "r", encoding="utf-8") as f:
#     T = json.load(f)
    
# T3 = T[:3000]
    
#%% UTM Description
states, symbols, transitions, q_accept, blank_symbol = read_turing_machine_from_txt("TuringMachines/UTM_aykut.txt")

#%% Simulated TM Description
M = TMDescriptor(Q=['q0', 'q1',  'q2',  'q3',  'q4',  'q5', 'q6',  'q7',  'q8',  'q9', 'end'], 
                 sigma=['#', '0', '1', 'A', 'B'], 
                 gamma=['#', '0', '1', 'A', 'B'], 
                 delta = {('q0', '#'): ('q0', '#', 'R'),
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
                          ('q9', '1'): ('end', '1', 'R')},
                 q0='q0', 
                 q_accept='end',
                 blank_symbol='#')

T = '00000011#00001000'
# T = '111_11'

E = BinaryTMEncoder(M)
encoded_machine = E.encode()  #encoded machine description
encoded_tape = E.encode_tape(T)



#%% Verstaile Shift
initial_state='INIT'
initial_tape = E.encode_all(encoded_machine, encoded_tape)

initial_tape = '0'*10 + E.encode_all(encoded_machine, encoded_tape) + '0'*10
tape_index = initial_tape.index('Z') - 1

encoded_halting_state = E.encoded_halting_state()

vs = TMVersatileShift(states, symbols, transitions, q_accept, blank_symbol)

# print('[INFO] Encoded Initial UTM Tape: ' + initial_tape)
# vs.simulate(initial_state, initial_tape, max_steps=20000000, utm=True, utm_encoded_halting_state=encoded_halting_state)

# # print decoded tape
# s = list(vs.s)[10:-10]
# s.pop(s.index('CP_CLN'))
# s.pop(s.index('.'))
# final_tape = ''.join(list(s)[tape_index:]).replace('Z', '0')
# decoded_tape = E.decode_tape(final_tape)

#%% Gödel Encoder    
godel_encoder = RationalGodelEncoder(states, symbols)

#%% NDA
nda = TMNonlinearDynamicalAutomaton(godel_encoder, vs)
# nda.simulate(initial_state, initial_tape, max_steps=12000000, verbose=False, utm=True, encoded_utm_halting_state=encoded_halting_state)

#%%
# final_tape = nda.decode_tm_tape(0, 1000)
# final_readout = final_tape[tape_index:].replace('Z', '0')
# decoded_tape = E.decode_tape(final_readout)

#%% RNN
initial_x, initial_y = nda.initialize(initial_state, initial_tape, 10)

# rnn = NDAtoRANN(nda)
rnn = FastNDAtoRANN(nda)
traj = rnn.simulate(initial_x, initial_y, max_steps=12000000, verbose=False,
                    utm=True, encoded_utm_halting_state=encoded_halting_state)