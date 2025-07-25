#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 30 19:23:03 2025

@author: gelenag

https://people.cs.uchicago.edu/~simon/OLD/COURSES/CS311/UTM.pdf

> buffer | machine desc | tape desc
"""
import re
import time
import random
import string
from datetime import datetime
from tqdm import tqdm

class CopyingMachine:
    def __init__(self, tape_description):
        self.tape = tape_description
        
    def execute(self):
        pass
    
#%% Turing Machine
class TuringMachine:
    def __init__(self, descriptor, tape, encoded_halting_state=None):
        
        self.description = descriptor
        self.tape = tape
        
        self.state = 'INIT'
        self.head_position = descriptor.initial_head_position
        
        self.encoded_halting_state = encoded_halting_state
    
    def replace_symbol(self, new_value):
        self.tape = self.tape[:self.head_position] + new_value + self.tape[self.head_position + 1:] 
    
    def read_tape(self):
        return self.tape[:self.head_position] + '[' + self.tape[self.head_position] + ']' + self.tape[self.head_position + 1:] 
    
    def read_simulated_tape(self, tape_index):
        return self.tape[tape_index:].replace('Z', '0')
    
    def read_condition(self):
        return (self.state, self.tape[self.head_position])
    
    def show_tape(self):
        print(self.read_tape())
        
    def show_condition(self):
        print(self.read_condition())
            
    def step(self):          
        current_symbol = self.tape[self.head_position]
        if (self.state, current_symbol) in self.description.delta:
            new_state, write_symbol, direction = self.description.delta[(self.state, current_symbol)]

            self.state = new_state
            self.replace_symbol(write_symbol)

            if direction == 'R':
                self.head_position += 1
            elif direction == 'L':
                self.head_position -= 1
            
            # ?????
            if self.head_position < 0:
                raise NotImplementedError()
            elif self.head_position >= len(self.tape):
                raise NotImplementedError()
        else:
            print((self.state, current_symbol))
            raise SystemError
                
        return True
    
    def execute(self, max_steps=100, log=False):        
        init_print_flag = True
        
        for i in tqdm(range(max_steps)):
            self.i = i                
            
            if self.state == 'CP_CLN':  # after copy
                buf_len = 20 
                if init_print_flag:
                    buff = self.tape[self.tape.index('X')+1:self.tape.index('X')+buf_len]
                    # print(f'Current Enc. State: {buff.split("0")[0]}')
                    # print(self.tape)
                    init_print_flag = False
                
                if self.tape[1:buf_len+1].split('0')[0] == '111111111':
                    aykut = 2
                
                if buff.split('0')[0] == self.encoded_halting_state:
                    print('Halt!')
                    print(f'TM executed successfully, TotalSteps: {i}')
                    break
            else:
                init_print_flag = True
                
                
            self.step()
        
        

            
#%% Old. Abstract Turing Machine
class UniversalTuringMachine:
    def __init__(self, machine_description, tape_description, halting_state):
        self._alphabet = ['0', '1', 'X', 'Y', 'Z', 'B']
        self._blank_symbol = '0'
        # self.all_dir_symbols = ['L', 'N', 'R']
        # self.encoded_dir_symbols = ['1', '11', '111']
        
        
        self.buffer_len = 20
        
        self.tape_index = len('X'+self.buffer_len*self._blank_symbol +'Y' + machine_description + '000' + 'Z')
        
        self.tape = 'X'+self.buffer_len*self._blank_symbol +'Y' + machine_description + '000' + 'Z' + tape_description
        
        self.head_position = self.buffer_len+1
        
        self.halting_state = halting_state
        
    def show_tape(self):
        show = self.tape[:self.head_position] + '[' + self.tape[self.head_position] + ']' + self.tape[self.head_position + 1:] 
        print(show)
        # print(self.tape)
        print('-----------------------------')
        
    def replace_symbol(self, new_value):
        self.tape = self.tape[:self.head_position] + new_value + self.tape[self.head_position + 1:] 
        
    def find_right(self, symbol):
        while self.tape[self.head_position] != symbol:
            self.head_position += 1
        
    def find_left(self, symbol):
        while self.tape[self.head_position] != symbol:
            self.head_position -= 1    
            if self.head_position < 0:
                return False
        return True
    
    def find_right_upto(self, symbol, upto, or_upto=None):
        while self.tape[self.head_position] != symbol:
            self.head_position += 1
            if or_upto is not None:
                if self.tape[self.head_position] == upto or self.tape[self.head_position] == or_upto:
                    return False
            else:
                if self.tape[self.head_position] == upto:
                    return False
            
        return True
    
    def find_leftmost_machinedesc(self):
        self.head_position = self.buffer_len+1
        
    def copying_machine(self, find):        
        while True:
            self.find_right(find)
            
            # found Y, find first 1
            self.head_position += 1
            
            while self.tape[self.head_position] == 'B':
                self.head_position += 1

            # 2. adım: Y'den sonraki ilk 1'i bul, eğer 0 ise 3. basamağa git
            if self.tape[self.head_position] == '1':
                self.replace_symbol('B')
                
                # find x and replace first 0 to 1                
                self.find_left('X')    #find to left
                    
                self.find_right('0')
                    
                self.replace_symbol('1')
            
                continue
            
            elif self.tape[self.head_position] == '0':
                # found 0, initiate cleanup
                # replace all Bs to 1
                self.head_position -= 1
                
                while True:
                    if self.tape[self.head_position] == find:
                        break
                    elif self.tape[self.head_position] == 'B':
                        self.replace_symbol('1')
                        
                    self.head_position -= 1
                    
                break  
            
    def match(self):
        """
        Step 1a: Move to the right and stop at the first 1. Mark this cell with a
        B. (If no “1” is found, that is, we reach either Y or a blank cell, then go to
        Step 2.)
        
        Step 1b: Move to the right until the head reaches Y .
    
        Step 1c: Move to the right and stop at the first 1. Mark this cell with a B.
        (If no “1” is found, that is, we reach a blank cell, then go to Step 3.)
        
        Step 1d: Move to the left and stop at X. Go to Step 1a.
        
        Step 2: Move to the right until the head reaches Y . Continue to the right
        and find the first 1. Return to X, and terminate in state qn . (If no “1” is
        found, that is, we reach a blank cell, then return to X and terminate in state
        qm .)
        
        Step 3: Move to the left until the head reaches X, and then terminate in
        state qn .
        """
        while True:
            self.find_left('X')
            if self.find_right_upto('1', 'Y', '0'):
                self.replace_symbol('B')
                self.find_right('Y')
                if self.find_right_upto('1', '0'):
                    self.replace_symbol('B')
                    continue
                else:
                    #step3
                    self.find_left('X')
                    return False # no match found
            else:
                # step2
                self.find_right('Y')
                if self.find_right_upto('1', '0'):
                    self.find_left('X')
                    return False # no match found
                else:
                    self.find_left('X')
                    # print('esleme bulubdu')
                    return True # match found
    
    #TODO: Fix me
    def matching_machine(self):
        first_term_matched = self.match()
        if first_term_matched:
            second_term_matched = self.match()
            
    def magic_replace(self, start, end, replacement):
        string_list = list(self.tape)
        string_list[start:end] = list(replacement) 
        modified_string = ''.join(string_list)
        self.tape = modified_string
            
    def magic_find(self, search_pattern): 
        found_patterns = list(re.finditer(search_pattern, self.tape))
        
        valid_matches = []
        for match in found_patterns:
            # Eşleşmenin başından önceki karakterleri kontrol et, sonu 0 ile bitmeli
            if match.start()-2 > 0:
                if self.tape[match.start()-2:match.start()] == "00" or self.tape[match.start()-1:match.start()] == "Y":
                    if self.tape[match.end()] == '0' and match.start() < self.tape_index:
                        valid_matches.append(match)
        
        # Eğer 2 tane eşleşme bulmuşsak
        if len(valid_matches) == 1:
            matched_string = valid_matches[0].group()  
            modified_string = matched_string.replace('0', 'Y')
            #### TODO:FİXME!!
            self.tape = self.tape.replace('Y', '0')
            self.magic_replace(valid_matches[0].start(), valid_matches[0].end(), modified_string)
        else:
            raise SystemError
            
    def read_symbol(self):
        return self.tape[self.head_position]
    
    def read_buffer(self):
        return self.tape[1:self.buffer_len+1]
    
    def read_tape(self, remove_head=True):
        if remove_head:
            return self.tape[self.tape_index:].replace('Z', '0')
        else:
            return self.tape[self.tape_index:]
        
    def magic_get_item(self):
        start = self.head_position
        if self.read_symbol() == '0':
            self.head_position += 1
        self.find_right('0')
        end = self.head_position
        item = self.tape[start+1:end]
        return item
    
    def erease_buffer(self):
        self.find_left('X')
        self.magic_replace(0, self.buffer_len+1,  'X'+self.buffer_len*self._blank_symbol)
        
    def shift_marker_right(self, marker):
        if not self.find_right(marker):
            self.find_left(marker)
            
        self.replace_symbol('0')
        self.head_position += 1
        self.find_right('0')
        self.replace_symbol(marker)
    
    def shift_marker_left(self, marker):
        if not self.find_left(marker):
            self.find_right(marker)
        
        if marker == 'Z':
            # check if we at the right end of the tape
            if self.head_position < self.tape_index:
                self.tape = self.tape[:self.tape_index-1] + '01' + self.tape[self.tape_index-1:] #add blank before Z
                self.head_position += 2
                
            
        self.replace_symbol('0')
        self.head_position -= 1
        self.find_left('0')
        self.replace_symbol(marker)

    def magic_replace_tape(self):
        self.find_right('Y')
        item_Y = self.magic_get_item()
        
        self.find_right('Z')
        items_Z = self.tape[self.head_position+1:].split('0')
        items_Z[0] = item_Y
        
        new_Z = '0'.join(items_Z)
        self.magic_replace(self.head_position+1, len(self.tape), new_Z)
        
    def read_current_state(self):
        cs = self.read_buffer().rstrip('0')
        return cs
        
    def execute_once(self):    
        self.copying_machine('Y')
        
        cs = self.read_current_state()
        #FIXME: possible verbose
        # print(f"Current State: {cs}")
        if cs == self.halting_state:
            return False
        
        # mark aux X            
        self.find_left('X')
        self.find_right('0')
        self.replace_symbol('X')
        
        #find Y and replace to 0
        self.find_right('Y')
        self.replace_symbol('0')
        
        self.find_right('Z')
        
        # check if we at the right end of the tape
        if self.head_position == len(self.tape)-1:
            self.tape += '10' #add one blank at the end 
            

        self.copying_machine('Z')
        
        print(f"Buffer: {self.read_buffer().rstrip('0')}")
        
        #step3
        self.find_left('X')
        self.replace_symbol('0')
        
        self.find_leftmost_machinedesc()
        self.replace_symbol('Y')
        
        #step4: search for quintuple
        # self.matching_machine()
        # self.magic_find('1011111')
        
        current_buffer = self.read_buffer().rstrip('0')
        self.magic_find(current_buffer)
        
        #step5: erease buffer
        self.erease_buffer()
        # self.show_tape()
        self.shift_marker_right('Y')
        self.shift_marker_right('Y')
        
        #step6:
        self.magic_replace_tape()
       
        
       
        
        #step7:
        self.find_left('Y')
        self.find_right('0')
        direction = self.magic_get_item()
        
        if direction == '111':
            self.shift_marker_right('Z')
        elif direction == '1':
            self.shift_marker_left('Z')
        else:
            pass #neither, stay
            
        print(f'Tape  : {self.read_tape(False)}')    
        
        #step8
        self.shift_marker_left('Y')
        
        # self.show_tape()
        
        return True
    
    def execute(self, max_steps=100):    
        for i in range(max_steps):
            if self.execute_once():
                continue
            else:
                print('Halt!')
                break