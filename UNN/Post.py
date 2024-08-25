#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 24 13:59:34 2024

@author: gelenag
"""
import re

class System:
    def __init__(self, alphabet, production, verbose=False):
        self.verbose = verbose
        self.alphabet = alphabet
        self.production = production
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


class BiTagSystem(System):
    def __init__(self, alphabet, production, verbose=False):
        super().__init__(alphabet, production, verbose)
        self.parse_production()
        
    def parse_string(self, input_string):
        pattern = '|'.join(re.escape(tag) for tag in self.alphabet+['*'])
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
        prod_id = self.alphabet.index(parsed_input[0])
        # remove first two
        parsed_input.pop(0)
        parsed_input.pop(0)
        # apply production by prod_id
        tobe_append = [i for i in self.parsed_production[prod_id][1]]
        parsed_input += tobe_append
        op = parsed_input
        
        if parsed_input[0] == self.halt_prod_symbol:
            halt = True
        else:
            halt = False
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
