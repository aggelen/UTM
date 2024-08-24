#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 24 13:59:34 2024

@author: gelenag
"""
import re

class PostCanonicalSystem:
    def __init__(self, alphabet, production):
        self.alphabet = alphabet
        self.production = production
        self.parse_production()
        #TODO: add axiom?

    def parse_production(self):
        self.production_lhs = []
        self.production_rhs = [] 
        
        for p in self.production:
            lhs, rhs = p.split(' -> ')
            self.production_lhs.append(lhs)
            self.production_rhs.append(rhs)


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

