#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 26 12:54:07 2025

@author: gelenag
"""

from UniversalRNN import TMGeneralizedShift, UTM_NonlinearDynamicalAutomaton, RNN
from Encoders import GodelEncoder

#%% UTM Description
def read_program(file_path):
    delta = {}
    states = set()  # Durumlar seti
    symbols = set()  # Semboller seti

    # Dosyayı açıyoruz
    with open(file_path, 'r') as file:
        for line in file:
            # Satırdaki boşlukları ayırıyoruz
            parts = line.strip().split('\t')
            
            # Geçiş bilgilerini ayıklıyoruz
            current_state = parts[0]
            symbol = parts[1]
            next_state = parts[2]
            write_symbol = parts[3]
            direction = parts[4]
            
            delta[(current_state, symbol)] = (next_state, write_symbol, direction)
            
            states.add(current_state)
            states.add(next_state)
            symbols.add(symbol)
            symbols.add(write_symbol)
            
    # print(f"No States: {len(sorted(states))}")

    return sorted(states), sorted(symbols), delta

states, symbols, transitions = read_program('../Programs/aykut_utm.txt')

#%% Turing Machine to Versatile Shift
GS = TMGeneralizedShift(states, symbols, transitions)

#%% Gödelization
GE_q = GodelEncoder(states)
GE_s = GodelEncoder(symbols)

# qf = GE_q.encode(GS.alpha_dod)

#%% Nonlinear Dynamical Automaton
NDA = UTM_NonlinearDynamicalAutomaton(GS, None, None)

#%% NDA to RNN
RNN = RNN(NDA)














