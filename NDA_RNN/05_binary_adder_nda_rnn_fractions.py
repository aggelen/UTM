#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 26 12:54:07 2025

@author: gelenag
"""

from NeuralUTM.SymbolicDynamics import TMVersatileShift
from NeuralUTM.Encoders import GodelEncoder, RationalGodelEncoder
from NeuralUTM.Automata import TMNonlinearDynamicalAutomaton, create_transition_animation
from NeuralUTM.NN import FastNDAtoRANN

from NeuralUTM.Helpers import read_turing_machine_from_txt

#%% TM Description
states, symbols, transitions, q_accept, blank_symbol = read_turing_machine_from_txt("TuringMachines/binary_adder.txt")

#%% Verstaile Shift
initial_state='q0'
initial_tape='00000011#00001000'
vs = TMVersatileShift(states, symbols, transitions, q_accept, blank_symbol)
# vs.simulate(initial_state, initial_tape)

#%% Gödel Encoder    
godel_encoder = RationalGodelEncoder(states, symbols)

#%% NDA
nda = TMNonlinearDynamicalAutomaton(godel_encoder, vs)
# nda.simulate(initial_state, initial_tape, max_steps=200)

#%% RNN
initial_x, initial_y = nda.initialize(initial_state, initial_tape, 10)

# %%
rnn = FastNDAtoRANN(nda)

traj = rnn.simulate(initial_x, initial_y, max_steps=200)





