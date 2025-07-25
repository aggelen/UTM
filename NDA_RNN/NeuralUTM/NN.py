#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 12 23:05:57 2025

@author: gelenag
"""

from bisect import bisect_right
from tqdm import tqdm
from gmpy2 import mpq
from itertools import chain
import numpy as np

def fmt_frac(f: mpq, precision: int = 6) -> str:
    sign = '-' if f < 0 else ''
    f = abs(f)
    integer = f.numerator // f.denominator
    rem = f.numerator % f.denominator
    dec_digits = []
    for _ in range(precision):
        rem *= 10
        dec_digits.append(str(rem // f.denominator))
        rem %= f.denominator
    return f"{sign}{integer}." + "".join(dec_digits)

def H(u):
    # u: mpq
    return mpq(1) if float(u) >= 0 else mpq(0)

def R(u):
    return u if u >= 0 else mpq(0)

class FastNDAtoRANN:
    def __init__(self, nda):
        self.nda = nda
        # precompute bounds as mpq lists
        self.x_bounds = [mpq(x) for x in nda.x_leftbounds]
        self.y_bounds = [mpq(y) for y in nda.y_leftbounds]
        self.m = len(self.x_bounds)
        self.n = len(self.y_bounds)

        self.extract_affine_from_nda()
        self.build_synaptic_weights()
        self.compute_inhibition_bias()

        # cache half h
        self.h2 = self.h / mpq(2)

        # MCL başlangıç potansiyelleri
        self.cx = mpq(0)
        self.cy = mpq(0)
        
        self._lam_x_arr = np.array(self.lambda_x, dtype=object)
        self._off_x_arr = np.array(self.offset_x, dtype=object)
        self._lam_y_arr = np.array(self.lambda_y, dtype=object)
        self._off_y_arr = np.array(self.offset_y, dtype=object)

    def extract_affine_from_nda(self):
        m, n = self.m, self.n
        self.lambda_x = [[mpq(0)]*n for _ in range(m)]
        self.offset_x = [[mpq(0)]*n for _ in range(m)]
        self.lambda_y = [[mpq(0)]*n for _ in range(m)]
        self.offset_y = [[mpq(0)]*n for _ in range(m)]
        # fill only defined cells
        xb_list = self.nda.x_leftbounds
        yb_list = self.nda.y_leftbounds
        for (xk, yk), ((lx, ax), (ly, ay)) in self.nda.cells.items():
            i = xb_list.index(xk)
            j = yb_list.index(yk)
            self.lambda_x[i][j] = mpq(lx)
            self.offset_x[i][j] = mpq(ax)
            self.lambda_y[i][j] = mpq(ly)
            self.offset_y[i][j] = mpq(ay)

    def build_synaptic_weights(self):
        m, n = self.m, self.n
        self.W_bslx = [[mpq(1), mpq(0)] for _ in range(m)]
        self.b_bslx = [-x for x in self.x_bounds]
        self.W_bsly = [[mpq(0), mpq(1)] for _ in range(n)]
        self.b_bsly = [-y for y in self.y_bounds]

    def compute_inhibition_bias(self):
        m, n = self.m, self.n
        max_x_f = float(max(self.nda.x_leftbounds))
        max_y_f = float(max(self.nda.y_leftbounds))
        max_x = mpq(max_x_f)
        max_y = mpq(max_y_f)
        # compute hx, hy over all cells
        hx = hy = None
        off_x, lam_x = self.offset_x, self.lambda_x
        off_y, lam_y = self.offset_y, self.lambda_y
        for i in range(m):
            row_off_x, row_lam_x = off_x[i], lam_x[i]
            row_off_y, row_lam_y = off_y[i], lam_y[i]
            for j in range(n):
                val_x = row_off_x[j] + row_lam_x[j] * max_x
                val_y = row_off_y[j] + row_lam_y[j] * max_y
                if hx is None or val_x > hx: hx = val_x
                if hy is None or val_y > hy: hy = val_y
        M = hx if hx >= hy else hy
        self.h = M * mpq(2)
    
    def step2_vec(self, verbose, t):
        """
        Vectorized BSL + LTL + keep-max + MCL in one go.
        """
        # 1) Cache locals
        cx, cy = self.cx, self.cy
        zero = mpq(0)
        one  = mpq(1)
    
        # 2) BSL → bx, by via bisect (O(log n)+O(n))
        kx = bisect_right(self.x_bounds, cx)
        bx = [one]*kx + [zero]*(self.m - kx + 1)
        ky = bisect_right(self.y_bounds, cy)
        by = [one]*ky + [zero]*(self.n - ky + 1)
    
        # 3) Bx, By differences (still O(n))
        h2 = self.h2
        Bx = [h2 * (bx[i]   - bx[i+1]) for i in range(self.m)]
        By = [h2 * (by[j]   - by[j+1]) for j in range(self.n)]
    
        # 4) Vectorized LTL + keep-max + MCL
        # — expand to arrays
        Bx_arr = np.array(Bx, dtype=object)            # shape (m,)
        By_arr = np.array(By, dtype=object)            # shape (n,)
    
        # — compute base streams
        Vx = self._lam_x_arr * cx + self._off_x_arr - self.h  # shape (m,n)
        Vy = self._lam_y_arr * cy + self._off_y_arr - self.h  # shape (m,n)
    
        # — add Bij = Bx[i] + By[j]
        total_x = Vx + Bx_arr[:, None] + By_arr[None, :]
        total_y = Vy + Bx_arr[:, None] + By_arr[None, :]
    
        # — apply threshold (no-move = zero)
        ge0 = np.frompyfunc(lambda v: v >= 0, 1, 1)
        tx = np.where(ge0(total_x), total_x, zero)
        ty = np.where(ge0(total_y), total_y, zero)
    
        # — flatten, find max and sum ties
        flat_tx = tx.ravel()
        flat_ty = ty.ravel()
        Mx = max(flat_tx)
        sum_x = sum(val for val in flat_tx if val == Mx)
        My = max(flat_ty)
        sum_y = sum(val for val in flat_ty if val == My)
    
        # 5) Update potentials & record
        self.cx, self.cy = sum_x, sum_y
        self.traj.append((self.cx, self.cy))
    
        # 6) Cell lookup & print
        i, j = self.nda.check_cell(self.cx, self.cy)
        if verbose:
            print(f"{t:5d} | cx={fmt_frac(self.cx)} | cy={fmt_frac(self.cy)}")
        return i, j
    
    def step2_vec2(self, verbose, t):
        """
        Vectorized BSL + LTL + keep-max + MCL in one go.
        """
        # 1) Kısa yollar
        cx, cy = self.cx, self.cy
        zero, one = mpq(0), mpq(1)

        # 2) BSL: bisect_right ile tek adımda bx, by
        m, n = self.m, self.n
        kx = bisect_right(self.x_bounds, cx)
        bx_arr = np.empty(m+1, dtype=object)
        bx_arr[:kx] = one
        bx_arr[kx:] = zero

        ky = bisect_right(self.y_bounds, cy)
        by_arr = np.empty(n+1, dtype=object)
        by_arr[:ky] = one
        by_arr[ky:] = zero

        # 3) Bx, By farkları: tam vektörlenebilir
        h2 = self.h2
        Bx_arr = h2 * (bx_arr[:-1] - bx_arr[1:])  # shape (m,)
        By_arr = h2 * (by_arr[:-1] - by_arr[1:])  # shape (n,)

        # 4) LTL + Bij + keep‐max + MCL
        #    Vx, Vy (shape m×n)
        Vx = self._lam_x_arr * cx + self._off_x_arr - self.h
        Vy = self._lam_y_arr * cy + self._off_y_arr - self.h

        #    Bij eklemesi (broadcast)
        total_x = Vx + Bx_arr[:, None] + By_arr[None, :]
        total_y = Vy + Bx_arr[:, None] + By_arr[None, :]

        #    negatifleri sıfıra döndür (no‐move)
        #    np.where boolean mask’i C-optimized iç döngüsü kullanır
        tx = np.where(total_x >= 0, total_x, zero)
        ty = np.where(total_y >= 0, total_y, zero)

        #    flatten → max ve eşit olanları topla
        flat_tx = tx.ravel()
        flat_ty = ty.ravel()
        Mx = max(flat_tx)
        My = max(flat_ty)
        sum_x = sum(v for v in flat_tx if v == Mx)
        sum_y = sum(v for v in flat_ty if v == My)

        # 5) Potansiyelleri güncelle ve kaydet
        self.cx, self.cy = sum_x, sum_y
        self.traj.append((self.cx, self.cy))

        # 6) Hücre bul ve yazdır
        i, j = self.nda.check_cell(self.cx, self.cy)
        if verbose:
            print(f"{t:5d} | cx={fmt_frac(self.cx)} | cy={fmt_frac(self.cy)}")
        return i, j
        
    def step2(self, verbose, t):
        """
        Single‐pass BSL + LTL + keep_max + MCL for one time‐step.
        Returns the (i, j) cell indices after updating cx, cy.
        """
        # 1) Cache locals
        xb, yb       = self.x_bounds,    self.y_bounds
        lam_x, off_x = self.lambda_x,    self.offset_x
        lam_y, off_y = self.lambda_y,    self.offset_y
        m, n         = self.m,           self.n
        cx, cy       = self.cx,          self.cy
        h, h2        = self.h,           self.h2
        zero         = mpq(0)
    
        # 2) BSL → bx, by
        bx = []
        for xi in xb:
            bx.append(mpq(1) if (cx - xi) >= 0 else zero)
        bx.append(zero)
    
        by = []
        for yj in yb:
            by.append(mpq(1) if (cy - yj) >= 0 else zero)
        by.append(zero)
    
        # 3) Bx, By differences
        Bx = [h2 * (bx[i]   - bx[i+1]) for i in range(m)]
        By = [h2 * (by[j]   - by[j+1]) for j in range(n)]
    
        # 4) LTL + keep_all_global_max + MCL in one pass
        Mx = My = None
        sum_x = zero
        sum_y = zero
    
        for i in range(m):
            bix         = Bx[i]
            lx_row, ax  = lam_x[i], off_x[i]
            ly_row, ay  = lam_y[i], off_y[i]
            for j in range(n):
                Bij = bix + By[j]
    
                # x‐stream
                vx = lx_row[j]*cx + ax[j] - h + Bij
                tx = vx if vx >= 0 else zero
                if Mx is None or tx > Mx:
                    Mx, sum_x = tx, tx
                elif tx == Mx:
                    sum_x += tx
    
                # y‐stream
                vy = ly_row[j]*cy + ay[j] - h + Bij
                ty = vy if vy >= 0 else zero
                if My is None or ty > My:
                    My, sum_y = ty, ty
                elif ty == My:
                    sum_y += ty
    
        # 5) Update potentials & record
        self.cx, self.cy = sum_x, sum_y
        self.traj.append((self.cx, self.cy))
    
        # 6) Cell lookup and optional verbose print
        i, j = self.nda.check_cell(self.cx, self.cy)
        if verbose:
            print(f"{t:5d} | cx={fmt_frac(self.cx)} | cy={fmt_frac(self.cy)}")
        return i, j
    
    def simulate(self, initial_x, initial_y, max_steps=200,
             verbose=True, utm=False, encoded_utm_halting_state=None):
        
        self.cx = mpq(initial_x)
        self.cy = mpq(initial_y)
        if verbose:
            print(f"Init → cx={fmt_frac(self.cx)}, cy={fmt_frac(self.cy)}")
        self.traj = [(self.cx, self.cy)]
    
        # _step = self.step2
        _step = self.step2_vec2
        
        decode_alpha = self.nda.encoder.decode_alpha
        decode_beta  = self.nda.encoder.decode_beta
    
        for t in tqdm(range(max_steps)):

            if utm:
                state = decode_alpha(self.cx, 0)[0]
                if state == 'CP_CLN':
                    buff = decode_beta(self.cy, 200)
                    if 'X' in buff:
                        est = ''.join(buff[buff.index('X')+1:]).split('0')[0]
                        if est == encoded_utm_halting_state:
                            print(f"[UTM HALT] Detected halting at step {t}")
                            self.nda.decode_tm_tape()
                            return self.traj
    
            # perform one step
            i, j = _step(verbose, t)
    
            # check accept‐cell
            if (i, j) in self.nda.accept_cells:
                _step(verbose, t+1)
                print(f"[HALT] Accept state reached at step {t+1}")
                self.nda.decode_xy(self.cx, self.cy)
                break
    
        return self.traj


    # def simulate(self, initial_x, initial_y, max_steps=200,
    #              verbose=True, utm=False, encoded_utm_halting_state=None):
    #     self.cx = mpq(initial_x)
    #     self.cy = mpq(initial_y)
    #     if verbose:
    #         print(f"Init → cx={fmt_frac(self.cx)}," 
    #               f" cy={fmt_frac(self.cy)}")
    #     self.traj = [(self.cx, self.cy)]

    #     _step = self.step2

    #     for t in tqdm(range(max_steps)):
    #         # optional UTM check...
    #         i, j = _step(verbose, t)
    #         if (i, j) in self.nda.accept_cells:
    #             _step(verbose, t+1)
    #             print(f"[HALT] Accept state reached at step {t+1}")
    #             self.nda.decode_xy(self.cx, self.cy)
    #             break

    #     return self.traj
    
    
    
# def fmt_frac(f: mpq, precision: int = 6) -> str:
#     """
#     f: Rational (mpq) nesnesi
#     precision: ondalık basamak sayısı
#     Returns: '123.456789' gibi bir string
#     """
#     sign = '-' if f < 0 else ''
#     f = abs(f)
#     integer = f.numerator // f.denominator
#     rem = f.numerator % f.denominator
#     dec_digits = []
#     for _ in range(precision):
#         rem *= 10
#         dec_digits.append(str(rem // f.denominator))
#         rem %= f.denominator
#     return f"{sign}{integer}." + "".join(dec_digits)

# def H(u):
#     # ε‐tolerant step function
#     return mpq(1) if float(u) >= 0 else mpq(0)

# def R(u):
#     return u if u >= 0 else mpq(0)

# class FastNDAtoRANN:
#     def __init__(self, nda):
#         self.nda = nda
#         # Precompute bounds
#         xb = [mpq(x) for x in nda.x_leftbounds]
#         yb = [mpq(y) for y in nda.y_leftbounds]
#         self.x_bounds = xb
#         self.y_bounds = yb
#         self.m = len(xb)
#         self.n = len(yb)

#         # Build full affine‐map grid with default zeros
#         lam_x = [[mpq(0)]*self.n for _ in range(self.m)]
#         off_x = [[mpq(0)]*self.n for _ in range(self.m)]
#         lam_y = [[mpq(0)]*self.n for _ in range(self.m)]
#         off_y = [[mpq(0)]*self.n for _ in range(self.m)]
#         for (xk, yk), ((lx, ax), (ly, ay)) in nda.cells.items():
#             i = nda.x_leftbounds.index(xk)
#             j = nda.y_leftbounds.index(yk)
#             lam_x[i][j] = mpq(lx)
#             off_x[i][j] = mpq(ax)
#             lam_y[i][j] = mpq(ly)
#             off_y[i][j] = mpq(ay)
#         self.lambda_x = lam_x
#         self.offset_x = off_x
#         self.lambda_y = lam_y
#         self.offset_y = off_y

#         # Compute inhibition bias h
#         max_x = mpq(float(max(nda.x_leftbounds)))
#         max_y = mpq(float(max(nda.y_leftbounds)))
#         hx = hy = None
#         for i in range(self.m):
#             row_lx, row_ax = lam_x[i], off_x[i]
#             row_ly, row_ay = lam_y[i], off_y[i]
#             for j in range(self.n):
#                 vx = row_ax[j] + row_lx[j] * max_x
#                 vy = row_ay[j] + row_ly[j] * max_y
#                 if hx is None or vx > hx: hx = vx
#                 if hy is None or vy > hy: hy = vy
#         M = hx if hx >= hy else hy
#         self.h = M * mpq(2)
#         self.h2 = self.h / mpq(2)

#         # Initial potentials
#         self.cx = mpq(0)
#         self.cy = mpq(0)

#     def check_cell(self, x, y):
#         i = bisect_right(self.x_bounds, x) - 1
#         j = bisect_right(self.y_bounds, y) - 1
#         return i, j

#     def BSL(self):
#         # Eq.(26)
#         half = self.h2
#         cx_f, cy_f = self.cx, self.cy
#         xb, yb = self.x_bounds, self.y_bounds

#         bx = [H(cx_f - xi) for xi in xb] + [mpq(0)]
#         by = [H(cy_f - yj) for yj in yb] + [mpq(0)]
#         Bx = [half * bx[i] - half * bx[i+1] for i in range(self.m)]
#         By = [half * by[j] - half * by[j+1] for j in range(self.n)]

#         return [[Bx[i] + By[j] for j in range(self.n)] for i in range(self.m)]

#     @staticmethod
#     def keep_all_global_max(mat):
#         flat = [v for row in mat for v in row]
#         M = max(flat)
#         return [[v if v == M else mpq(0) for v in row] for row in mat]

#     def LTL(self, B):
#         # Eq.(27)
#         m, n = self.m, self.n
#         cx_f, cy_f = self.cx, self.cy
#         h = self.h
#         lam_x, off_x = self.lambda_x, self.offset_x
#         lam_y, off_y = self.lambda_y, self.offset_y

#         Tx = [[None]*n for _ in range(m)]
#         Ty = [[None]*n for _ in range(m)]
#         for i in range(m):
#             row_lx, row_ax = lam_x[i], off_x[i]
#             row_ly, row_ay = lam_y[i], off_y[i]
#             row_B = B[i]
#             row_Tx, row_Ty = Tx[i], Ty[i]
#             for j in range(n):
#                 vx = row_lx[j] * cx_f + row_ax[j] - h + row_B[j]
#                 vy = row_ly[j] * cy_f + row_ay[j] - h + row_B[j]
#                 row_Tx[j] = vx if vx >= 0 else mpq(0)
#                 row_Ty[j] = vy if vy >= 0 else mpq(0)

#         return (self.keep_all_global_max(Tx),
#                 self.keep_all_global_max(Ty))

#     def MCL(self, Tx, Ty):
#         # Eq.(28)
#         total_x = mpq(0)
#         total_y = mpq(0)
#         for row in Tx:
#             for v in row:
#                 total_x += v
#         for row in Ty:
#             for v in row:
#                 total_y += v
#         self.cx = total_x if total_x >= 0 else mpq(0)
#         self.cy = total_y if total_y >= 0 else mpq(0)
    
#     def step(self, verbose, t):
#         B = self.BSL()
#         Tx, Ty = self.LTL(B)
#         self.MCL(Tx, Ty)
#         self.traj.append((self.cx, self.cy))
#         i, j = self.nda.check_cell(self.cx, self.cy)
#         if verbose:
#             print(f"{t:5d} | cx={fmt_frac(self.cx)} | cy={fmt_frac(self.cy)}")
#         return i, j
    
#     def simulate(self, initial_x, initial_y,
#                    max_steps=200, verbose=True,
#                    utm=False, encoded_utm_halting_state=None):

#           self.cx = mpq(initial_x)
#           self.cy = mpq(initial_y)
#           if verbose:
#               print(f"Init → cx={fmt_frac(self.cx)}, cy={fmt_frac(self.cy)}")
    
#           self.traj = [(self.cx, self.cy)]
#           check = self.nda.check_cell
#           decode_alpha = self.nda.encoder.decode_alpha
#           decode_beta  = self.nda.encoder.decode_beta
#           _step = self.step
    
#           for t in tqdm(range(max_steps)):
#               # If monitoring a UTM, check right before stepping
#               if utm:
#                   state = decode_alpha(self.cx, 0)[0]
#                   if state == 'CP_CLN':
#                       buff = decode_beta(self.cy, 200)
#                       if 'X' in buff:
#                           est = ''.join(buff[buff.index('X')+1:]).split('0')[0]
#                           if est == encoded_utm_halting_state:
#                               print(f"[UTM HALT] Detected UTM halting at step {t}")
#                               self.nda.decode_tm_tape()
#                               break
    
#               i, j = _step(verbose, t)
    
#               if (i, j) in self.nda.accept_cells:
#                   _step(verbose, t+1)
#                   print(f"[HALT] Accept state reached at step {t+1}")
#                   self.nda.decode_xy(self.cx, self.cy)
#                   break
    
#           return self.traj


        