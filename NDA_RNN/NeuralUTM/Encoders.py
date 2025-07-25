#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 11 20:16:47 2025

@author: gelenag
"""

#%% gödel
import itertools as itt
import numpy as np

class GodelEncoder:
    def __init__(self, states, symbols):
        # durum ve sembol listeleri
        self.states  = list(states)
        self.symbols = list(symbols)
        # Gödel numaraları (int)
        self.gamma_q = {q: i for i, q in enumerate(self.states)}
        self.gamma_s = {s: i for i, s in enumerate(self.symbols)}
        # boyutlar as longdouble
        self.nq = np.longdouble(len(self.states))
        self.ns = np.longdouble(len(self.symbols))
        # önbölme katsayıları
        self.inv_nq = np.longdouble(1) / self.nq
        self.inv_ns = np.longdouble(1) / self.ns

    def encode_alpha(self, alpha_reversed):
        """
        α′ already reversed: [state, sym1, sym2, ...].
        ψₓ(α′) = γ_q(state)/nq +
                 Σ_{k=1..} γ_s(sym_k)/(nq * ns^k)
        Returns a np.longdouble.
        """
        # ilk terim: durum
        st = alpha_reversed[0]
        val = np.longdouble(self.gamma_q[st]) * self.inv_nq

        # kuyruk sembolleri
        for k, sym in enumerate(alpha_reversed[1:], start=1):
            g = np.longdouble(self.gamma_s[sym])
            # γ_s(sym) * inv_nq * (inv_ns**k)
            val += g * self.inv_nq * (self.inv_ns ** k)

        return val

    def encode_beta(self, beta):
        """
        β normal: [sym1, sym2, ...].
        ψᵧ(β) = Σ_{k=1..} γ_s(sym_k)/ns^k
        Returns a np.longdouble.
        """
        val = np.longdouble(0)
        for k, sym in enumerate(beta, start=1):
            g = np.longdouble(self.gamma_s[sym])
            val += g * (self.inv_ns ** k)
        return val
    
    def decode_alpha(self, x, max_len=100):
        gamma_q_inv = dict((self.gamma_q[k], k) for k in self.gamma_q)
        gamma_s_inv = dict((self.gamma_s[k], k) for k in self.gamma_s)
        
        # gamma_q_inv = {v: k for k, v in self.gamma_q.items()}
        # gamma_s_inv = {v: k for k, v in self.gamma_s.items()}
        # blank = '#'  # ya da kendi blank_symbol'ün

        # 1) Durumu al
        v = x * self.nq + 1e-15
        idx_q = int(np.floor(v))
        alpha_rev = [gamma_q_inv[idx_q]]
        rem = v - idx_q

        # 2) tail sembollerini decode et, blank görünce dur
        for _ in range(max_len):
            v = rem * self.ns + 1e-15
            idx_s = int(np.floor(v))
            sym = gamma_s_inv[idx_s]
            alpha_rev.append(sym)
            rem = v - idx_s

        # Kullanırken terslediğin alpha'yı geri çevirebilirsin:
        return alpha_rev  # (terslenmiş halde)

    def decode_beta(self, y, max_len=100):
        gamma_s_inv = {v: k for k, v in self.gamma_s.items()}
        blank = '#'
        beta = []
        rem = y
        eps = 1e-9 
        
        for _ in range(max_len):
            v = rem * self.ns
            idx_s = int(np.floor(v))
            sym = gamma_s_inv[idx_s]
            beta.append(sym)
            rem = v - idx_s

        return beta
    
from mpmath import mp, mpf, floor

class MPFGodelEncoder:
    def __init__(self, states, symbols, precision=100):
        """
        states: iterable of durum isimleri
        symbols: iterable of semboller
        precision: ondalık basamak hassasiyeti (mp.dps)
        """
        # Hassasiyeti ayarla
        mp.dps = precision

        # durum ve sembol listeleri
        self.states  = list(states)
        self.symbols = list(symbols)

        # Gödel numaraları (int)
        self.gamma_q = {q: i for i, q in enumerate(self.states)}
        self.gamma_s = {s: i for i, s in enumerate(self.symbols)}

        # boyutlar as mpf
        self.nq = mpf(len(self.states))
        self.ns = mpf(len(self.symbols))

        # önbölme katsayıları
        self.inv_nq = mpf(1) / self.nq
        self.inv_ns = mpf(1) / self.ns

    def encode_alpha(self, alpha_reversed):
        """
        α′ already reversed: [state, sym1, sym2, ...].
        ψₓ(α′) = γ_q(state)/nq + Σ_{k≥1} γ_s(sym_k)/(nq * ns^k)
        Returns an mpf.
        """
        st = alpha_reversed[0]
        val = mpf(self.gamma_q[st]) * self.inv_nq

        for k, sym in enumerate(alpha_reversed[1:], start=1):
            g = mpf(self.gamma_s[sym])
            val += g * self.inv_nq * (self.inv_ns ** k)

        return val

    def encode_beta(self, beta):
        """
        β normal: [sym1, sym2, ...].
        ψᵧ(β) = Σ_{k≥1} γ_s(sym_k)/ns^k
        """
        val = mpf(0)
        for k, sym in enumerate(beta, start=1):
            g = mpf(self.gamma_s[sym])
            val += g * (self.inv_ns ** k)
        return val

    def decode_alpha(self, x, max_len=100):
        """
        x: mpf kod değeri
        Returns: reversed alpha list [state, sym1, sym2, ...]
        """
        inv_q = {v: k for k, v in self.gamma_q.items()}
        inv_s = {v: k for k, v in self.gamma_s.items()}

        # 1) Durumu al
        v = x * self.nq
        idx_q = int(floor(v))
        if idx_q not in inv_q:
            raise ValueError(f"decode_alpha: bilinmeyen idx_q={idx_q}")
        alpha_rev = [inv_q[idx_q]]
        rem = v - mpf(idx_q)

        # 2) Kuyruk sembolleri
        for _ in range(max_len):
            v = rem * self.ns
            idx_s = int(floor(v))
            if idx_s not in inv_s:
                break
            alpha_rev.append(inv_s[idx_s])
            rem = v - mpf(idx_s)

        return alpha_rev

    def decode_beta(self, y, max_len=100):
        """
        y: mpf kod değeri
        Returns: beta list [sym1, sym2, ...]
        """
        inv_s = {v: k for k, v in self.gamma_s.items()}
        beta = []
        rem = y

        for _ in range(max_len):
            v = rem * self.ns
            idx_s = int(floor(v))
            if idx_s not in inv_s:
                break
            beta.append(inv_s[idx_s])
            rem = v - mpf(idx_s)

        return beta
    
#%%
# from fractions import Fraction

# class RationalGodelEncoder:
#     def __init__(self, states, symbols):
#         """
#         states: iterable of state names
#         symbols: iterable of symbol names
#         All internal values are exact fractions.
#         """
#         # durum ve sembol listeleri
#         self.states  = list(states)
#         self.symbols = list(symbols)

#         # Gödel numaraları (int)
#         self.gamma_q = {q: i for i, q in enumerate(self.states)}
#         self.gamma_s = {s: i for i, s in enumerate(self.symbols)}

#         # boyutlar as Fraction
#         self.nq = Fraction(len(self.states), 1)
#         self.ns = Fraction(len(self.symbols), 1)

#         # önbölme katsayıları
#         self.inv_nq = Fraction(1, 1) / self.nq
#         self.inv_ns = Fraction(1, 1) / self.ns

#     def encode_alpha(self, alpha_reversed):
#         """
#         α′ already reversed: [state, sym1, sym2, ...].
#         ψₓ(α′) = γ_q(state)/nq + Σ_{k≥1} γ_s(sym_k)/(nq * ns**k)
#         Returns a Fraction.
#         """
#         st = alpha_reversed[0]
#         val = Fraction(self.gamma_q[st], 1) * self.inv_nq

#         for k, sym in enumerate(alpha_reversed[1:], start=1):
#             g = Fraction(self.gamma_s[sym], 1)
#             val += g * self.inv_nq * (self.inv_ns ** k)

#         return val

#     def encode_beta(self, beta):
#         """
#         β normal: [sym1, sym2, ...].
#         ψᵧ(β) = Σ_{k≥1} γ_s(sym_k)/ns**k
#         Returns a Fraction.
#         """
#         val = Fraction(0, 1)
#         for k, sym in enumerate(beta, start=1):
#             g = Fraction(self.gamma_s[sym], 1)
#             val += g * (self.inv_ns ** k)
#         return val

#     def decode_alpha(self, x, max_len=100):
#         """
#         x: Fraction code value
#         Returns: reversed alpha list [state, sym1, sym2, ...]
#         """
#         inv_q = {v: k for k, v in self.gamma_q.items()}
#         inv_s = {v: k for k, v in self.gamma_s.items()}

#         # 1) Durum
#         v = x * self.nq
#         idx_q = v.numerator // v.denominator
#         if idx_q not in inv_q:
#             raise ValueError(f"decode_alpha: unknown idx_q={idx_q}")
#         alpha_rev = [inv_q[idx_q]]
#         rem = v - Fraction(idx_q, 1)

#         # 2) Kuyruk sembolleri
#         for _ in range(max_len):
#             v = rem * self.ns
#             idx_s = v.numerator // v.denominator
#             if idx_s not in inv_s:
#                 break
#             alpha_rev.append(inv_s[idx_s])
#             rem = v - Fraction(idx_s, 1)

#         return alpha_rev

#     def decode_beta(self, y, max_len=100):
#         """
#         y: Fraction code value
#         Returns: beta list [sym1, sym2, ...]
#         """
#         inv_s = {v: k for k, v in self.gamma_s.items()}
#         beta = []
#         rem = y

#         for _ in range(max_len):
#             v = rem * self.ns
#             idx_s = v.numerator // v.denominator
#             if idx_s not in inv_s:
#                 break
#             beta.append(inv_s[idx_s])
#             rem = v - Fraction(idx_s, 1)

#         return beta

try:
    from gmpy2 import mpq as Rational
    print("Using gmpy2.mpq for rationals")
except ImportError:
    from fractions import Fraction as Rational
    print("Falling back to Fraction for rationals")

class RationalGodelEncoder:
    def __init__(self, states, symbols):
        """
        states: iterable of state names
        symbols: iterable of symbol names
        All internal values are exact Rational (mpq or Fraction).
        """
        # durum ve sembol listeleri
        self.states  = list(states)
        self.symbols = list(symbols)

        # Gödel numaraları (int)
        self.gamma_q = {q: i for i, q in enumerate(self.states)}
        self.gamma_s = {s: i for i, s in enumerate(self.symbols)}

        # boyutlar as Rational
        self.nq = Rational(len(self.states))
        self.ns = Rational(len(self.symbols))

        # önbölme katsayıları
        self.inv_nq = Rational(1) / self.nq
        self.inv_ns = Rational(1) / self.ns

    def encode_alpha(self, alpha_reversed):
        """
        α′ already reversed: [state, sym1, sym2, ...].
        ψₓ(α′) = γ_q(state)/nq + Σ_{k≥1} γ_s(sym_k)/(nq * ns**k)
        Returns a Rational.
        """
        st = alpha_reversed[0]
        val = Rational(self.gamma_q[st]) * self.inv_nq

        for k, sym in enumerate(alpha_reversed[1:], start=1):
            g = Rational(self.gamma_s[sym])
            val += g * self.inv_nq * (self.inv_ns ** k)

        return val

    def encode_beta(self, beta):
        """
        β normal: [sym1, sym2, ...].
        ψᵧ(β) = Σ_{k≥1} γ_s(sym_k)/ns**k
        Returns a Rational.
        """
        val = Rational(0)
        for k, sym in enumerate(beta, start=1):
            g = Rational(self.gamma_s[sym])
            val += g * (self.inv_ns ** k)
        return val

    def decode_alpha(self, x, max_len=100):
        """
        x: Rational code value
        Returns: reversed alpha list [state, sym1, sym2, ...]
        """
        inv_q = {v: k for k, v in self.gamma_q.items()}
        inv_s = {v: k for k, v in self.gamma_s.items()}

        # 1) Durum
        v     = x * self.nq
        idx_q = int(v)   # truncates toward zero
        if idx_q not in inv_q:
            raise ValueError(f"decode_alpha: unknown idx_q={idx_q}")
        alpha_rev = [inv_q[idx_q]]
        rem        = v - Rational(idx_q)

        # 2) Kuyruk sembolleri
        for _ in range(max_len):
            v     = rem * self.ns
            idx_s = int(v)
            if idx_s not in inv_s:
                break
            alpha_rev.append(inv_s[idx_s])
            rem = v - Rational(idx_s)

        return alpha_rev

    def decode_beta(self, y, max_len=100):
        """
        y: Rational code value
        Returns: beta list [sym1, sym2, ...]
        """
        inv_s = {v: k for k, v in self.gamma_s.items()}
        beta  = []
        rem   = y

        for _ in range(max_len):
            v     = rem * self.ns
            idx_s = int(v)
            if idx_s not in inv_s:
                break
            beta.append(inv_s[idx_s])
            rem = v - Rational(idx_s)

        return beta

#%%
class ShiftAddGodelEncoder:
    def __init__(self, states, symbols):
        # assign small ints
        self.gamma_q = {q:i for i,q in enumerate(states)}
        self.gamma_s = {s:i for i,s in enumerate(symbols)}
        # compute bit-widths
        self.bq = (len(states)-1).bit_length() or 1
        self.bs = (len(symbols)-1).bit_length() or 1
        # masks & reverse maps
        self.mask_q = (1<<self.bq) - 1
        self.mask_s = (1<<self.bs) - 1
        self.code2state = {i:q for q,i in self.gamma_q.items()}
        self.code2sym   = {i:s for s,i in self.gamma_s.items()}

    def encode_alpha(self, alpha_reversed: list) -> int:
        X = self.gamma_q[alpha_reversed[0]]
        for sym in alpha_reversed[1:]:
            X = (X << self.bs) | self.gamma_s[sym]
        return X

    def encode_beta(self, beta: list) -> int:
        X = 0
        for sym in beta:
            X = (X << self.bs) | self.gamma_s[sym]
        return X

    def decode_alpha(self, code: int, max_syms: int=1000) -> list:
        tmp = code
        syms = []
        # peel off tape symbols
        while tmp > self.mask_q and len(syms) < max_syms:
            c = tmp & self.mask_s
            if c not in self.code2sym:
                break
            syms.append(self.code2sym[c])
            tmp >>= self.bs
        state = self.code2state.get(tmp & self.mask_q)
        if state is None:
            raise ValueError(f"decode_alpha: unknown state code {tmp}")
        syms.reverse()
        return [state] + syms

    def decode_beta(self, code: int, max_syms: int=1000) -> list:
        tmp = code
        syms = []
        # peel off tape symbols
        while tmp and len(syms) < max_syms:
            c = tmp & self.mask_s
            if c not in self.code2sym:
                break
            syms.append(self.code2sym[c])
            tmp >>= self.bs
        syms.reverse()
        return syms