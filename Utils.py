#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 30 19:36:46 2025

@author: gelenag
"""

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
            
    print(f"No States: {len(sorted(states))}")

    return sorted(states), sorted(symbols), delta

def uniquify(input_list):
    seen = set()  
    unique_list = [] 

    for item in input_list:
        if item not in seen:
            unique_list.append(item)  
            seen.add(item)  
    return unique_list

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
        
        tape = 'X'+self.buffer_len*self._blank_symbol +'Y' + encoded_machine + '000' + 'Z' + encoded_tape + '0'
        
        return tape