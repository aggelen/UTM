#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 11 20:35:06 2025

@author: gelenag
"""

def write_turing_machine_to_txt(states, symbols, transitions, q_accept, blank_symbol, filename):
    with open(filename, 'w') as f:
        f.write(f"states: {','.join(states)}\n")
        f.write(f"symbols: {','.join(symbols)}\n")
        f.write(f"accept: {q_accept}\n")
        f.write(f"blank: {blank_symbol}\n")
        for (state, symbol), (next_state, write_symbol, direction) in transitions.items():
            f.write(f"({state},{symbol})->({next_state},{write_symbol},{direction})\n")
            
            
def read_turing_machine_from_txt(filename):
    with open(filename, 'r') as f:
        lines = f.read().splitlines()
    
    states = lines[0].split(":")[1].strip().split(",")
    symbols = lines[1].split(":")[1].strip().split(",")
    q_accept = lines[2].split(":")[1].strip()
    blank_symbol = lines[3].split(":")[1].strip()
    
    transitions = {}
    for line in lines[4:]:
        if not line.strip(): continue
        left, right = line.split("->")
        state, symbol = left.strip("()").split(",")
        next_state, write_symbol, direction = right.strip("()").split(",")
        transitions[(state, symbol)] = (next_state, write_symbol, direction)
    
    return states, symbols, transitions, q_accept, blank_symbol

def uniquify(input_list):
    seen = set()  
    unique_list = [] 

    for item in input_list:
        if item not in seen:
            unique_list.append(item)  
            seen.add(item)  
    return unique_list

class BinaryTMEncoder:
    def __init__(self, M):
        self.M = M
        self.all_symbols = uniquify(M.sigma + M.gamma)
        
        # blank must be first:
        self.all_symbols.sort(key=lambda x: x != self.M.blank_symbol)
        
        self.encoded_symbols = self.unary_encode(self.all_symbols)
        
        self.encoded_states = self.unary_encode(M.Q)
        self.all_dir_symbols = ['L', 'N', 'R']
        self.encoded_dir_symbols = ['1', '11', '111']
        
    @staticmethod
    def unary_encode(symbols):
        unary_list = []
        count = 1
        for i, symbol in enumerate(symbols):
            unary_list.append('1' * count)
            count += 1

        return unary_list
    
    def encoded_halting_state(self):
        
        return self.encoded_states[self.M.Q.index(self.M.q_accept)]
    
    def encode(self):
        print('Encoding machine ...')
        encoded_tm = ''
        for trans_key, trans_value in self.M.delta.items():
            qi, xi = trans_key
            qk, xl, dm = trans_value
            
            q_id, xi_id = self.M.Q.index(qi), self.all_symbols.index(xi)
            qk_id, xl_id, dm_id = self.M.Q.index(qk), self.all_symbols.index(xl), self.all_dir_symbols.index(dm)
            
            enc_qi , enc_xi = self.encoded_states[q_id], self.encoded_symbols[xi_id]
            enc_qk , enc_xl, enc_dm = self.encoded_states[qk_id], self.encoded_symbols[xl_id], self.encoded_dir_symbols[dm_id]
            
            encoded_transition = enc_qi+'0'+enc_xi+'0'+enc_qk+'0'+enc_xl+'0'+enc_dm+'00'
            encoded_tm += encoded_transition
        
        
        # print('Turing Machine Number:')
        # print(int(encoded_tm, 2))
        return encoded_tm
    
    def encode_tape(self, tape):
        print('Encoding tape ...')
        encoded_tape = ''
        for t in tape:
            encoded_tape += self.encoded_symbols[self.all_symbols.index(t)] + '0'
            
        print('Encoded Tape:')
        print(encoded_tape)
        return encoded_tape
    
    def decode_tape(self, tape):
        print('Decoding tape ...')
        decoded_tape = ''
        for t in tape.rstrip('0').split('0'):
            if t == '':
                continue
            t = t.replace('B', '1')
            decoded_tape += self.all_symbols[self.encoded_symbols.index(t)]
        
        decoded_tape = decoded_tape.strip(self.all_symbols[0])
        
        print('Decoded Tape:')
        print(decoded_tape)
        return decoded_tape
    
    def encode_all(self, encoded_machine, encoded_tape):
        self.buffer_len = 20
        self._alphabet = ['0', '1', 'X', 'Y', 'Z', 'B']
        self._blank_symbol = '0'
        
        # tape_index = len('X'+self.buffer_len*self._blank_symbol +'Y' + encoded_machine + '000' + 'Z')
        
        tape = 'X'+self.buffer_len*self._blank_symbol +'Y' + encoded_machine + '0'*10 + 'Z' + encoded_tape + '0'
        
        return tape
    
class TMDescriptor:
    def __init__(self, Q, sigma, gamma, delta, q0, q_accept, q_reject=None, blank_symbol=None, init_head_pos=0):
        # Q: Set of states
        # sigma: Input alphabet
        # gamma: Tape alphabet (including blank symbol)
        # delta: Transition function (dictionary)
        # q0: Initial state
        # q_accept: Accept state
        # q_reject: Reject state
        self.Q = uniquify(Q)
        self.sigma = uniquify(sigma)
        self.gamma = uniquify(gamma)
        self.delta = delta
        self.q0 = q0
        self.q_accept = q_accept
        self.q_reject = q_reject
        self.blank_symbol = blank_symbol   
        self.initial_head_position = init_head_pos
        
        #halting state must be last
        self.Q.sort(key=lambda x: x == self.q_accept)