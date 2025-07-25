#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 11 20:14:45 2025

@author: gelenag
"""
import numpy as np
import matplotlib.pyplot as plt
import imageio
from matplotlib import colors
from mpmath import mp
from bisect import bisect_right
from fractions import Fraction

try:
    from gmpy2 import mpq as Rational
    print("Using gmpy2.mpq for rationals")
except ImportError:
    from fractions import Fraction as Rational
    print("Falling back to Fraction for rationals")
from bisect import bisect_right
from tqdm import tqdm

from math import gcd
try:
    import gmpy2
except ImportError:
    gmpy2 = None

def lcm(a: int, b: int) -> int:
    """Compute least common multiple of two integers."""
    return abs(a * b) // gcd(a, b)

def get_denominator(r):
    """
    Extract the denominator from a rational number r.
    Supports fractions.Fraction (r.denominator) and gmpy2.mpq (via gmpy2.denom).
    """
    # fractions.Fraction
    if hasattr(r, 'denominator'):
        return r.denominator
    # gmpy2.mpq
    if gmpy2 is not None:
        try:
            return gmpy2.denom(r)
        except Exception:
            try:
                return gmpy2.denominator(r)
            except Exception:
                pass
    raise TypeError(f"Cannot extract denominator from {type(r)}")

def compute_lcm_denominators_with_keys(cell_dict) -> int:
    """
    Given a dict of the form:
      { (x_key, y_key): ((lambda_x, a_x), (lambda_y, a_y)), ... }
    where both keys (x_key, y_key) and values are rationals (mpq or Fraction),
    compute the LCM of all denominators present.
    """
    lcm_den = 1
    for (x_key, y_key), ((lambda_x, a_x), (lambda_y, a_y)) in cell_dict.items():
        for rat in (x_key, y_key, lambda_x, a_x, lambda_y, a_y):
            den = get_denominator(rat)
            lcm_den = lcm(lcm_den, den)
    return int(lcm_den)

def fmt_frac(f: Rational, precision: int = 6) -> str:
    """
    f: Rational nesnesi
    precision: ondalık basamak sayısı
    Returns: '123.456789' gibi bir string
    """
    # İşareti al
    sign = '-' if f < 0 else ''
    f = abs(f)
    # Tam kısım
    integer = f.numerator // f.denominator
    rem = f.numerator % f.denominator

    # Ondalık kısım
    dec_digits = []
    for _ in range(precision):
        rem *= 10
        dec_digits.append(str(rem // f.denominator))
        rem %= f.denominator

    return f"{sign}{integer}." + "".join(dec_digits)


#%%
def dyadic_params(lambda_rational: Fraction, a_rational: Fraction):
    """
    Convert dyadic Rational lambda_rational and a_rational into
    a single bit-shift and integer offset for x_new = lambda*x + a.
    Returns (shift, offset_int) such that:
      if shift>=0: x_new = x << shift
      else:         x_new = x >> -shift
      then x_new += offset_int
    """
    # Extract numerator and denominator (must be powers of two)
    Lnum = lambda_rational.numerator
    Lden = lambda_rational.denominator
    Anum = a_rational.numerator
    Aden = a_rational.denominator

    # Compute exponents: lambda_rational = 2^p / 2^q => shift = p - q
    p = (Lnum.bit_length() - 1) if Lnum and (Lnum & (Lnum - 1)) == 0 else 0
    q = (Lden.bit_length() - 1) if Lden and (Lden & (Lden - 1)) == 0 else 0
    shift = p - q

    # Align offset: a_rational * 2^shift = Anum * 2^(shift) / Aden
    # So offset_int = Anum << shift_minus_Aexp if shift>=Aexp
    diff = shift - (Aden.bit_length() - 1)
    if diff >= 0:
        offset_int = Anum << diff
    else:
        offset_int = Anum >> -diff

    return shift, offset_int

#%%
class TMNonlinearDynamicalAutomaton:
    def __init__(self, encoder, versatile_shift):
        self.encoder = encoder
        self.versatile_shift = versatile_shift
        self.cells = {}  # {(i, j): ((λ_x, a_x), (λ_y, a_y))}

        self.x_leftbounds = []
        self.y_leftbounds = []        
        self.accept_coords = []
        
        self.build_from_transitions()
               
        self.mark_accept_cells()
        
        self.x_leftbounds = sorted(self.x_leftbounds)
        self.y_leftbounds = sorted(self.y_leftbounds)
        
        self.state_traj = []
        
        self.denominator_lcm = compute_lcm_denominators_with_keys(self.cells)
        
        self._build_fixedpoint_cells()
        
    def _build_fixedpoint_cells(self):
        """Convert both cell keys and coefficients to fixed-point integers."""
        L = self.denominator_lcm
      
        # 1) Bound’ları integer’a çevir
        #    (bu listeler artık hücre anahtarlarınız olacak)
        self.x_bounds_int = [int(xk * L) for xk in self.x_leftbounds]
        self.y_bounds_int = [int(yk * L) for yk in self.y_leftbounds]
      
        # 2) Hücre katsayılarını ve anahtarlarını integer’a çevir
        self.cells_int = {}
        for (xk, yk), ((lambda_x, offset_x), (lambda_y, offset_y)) in self.cells.items():
            # orijinal anahtarların integer karşılıkları
            xk_int = int(xk * L)
            yk_int = int(yk * L)
            # katsayıların integer karşılıkları
            lambda_x_int = int(lambda_x * L)
            offset_x_int = int(offset_x * L)
            lambda_y_int = int(lambda_y * L)
            offset_y_int = int(offset_y * L)
            # yeni dict’e ekle
            self.cells_int[(xk_int, yk_int)] = (
                (lambda_x_int, offset_x_int),
                (lambda_y_int, offset_y_int)
            )

    def simulate_fixedpoint(self,
                           initial_state,
                           initial_tape,
                           max_steps=100,
                           buff_len=10,
                           verbose=True,
                           utm=False,
                           encoded_utm_halting_state=None):
        """
        Fixed-point simulate: integer aritmetiği + hücre-key tabanlı UTM-halt.
        """
        L = self.denominator_lcm
    
        # Görselleştirme dizileri (isteğe bağlı)
        self.vis_grid_shape = (len(self.x_bounds_int), len(self.y_bounds_int))
        self.vis_visited = []
    
        # 1) Başlangıç: rasyonel → integer
        x_r, y_r = self.initialize(initial_state, initial_tape, buff_len)
        
        # 2) Başlangıç paydalarını alın
        den_x = get_denominator(x_r)
        den_y = get_denominator(y_r)
    
        # 3) Etkin ortak payda
        L0 = self.denominator_lcm
        L0 = lcm(L0, den_x)
        L_eff = lcm(L0, den_y)
        
        
        # 4) integer bounds ve hücre haritası (L_eff altında)
        x_bounds = [int(xk * L_eff) for xk in self.x_leftbounds]
        y_bounds = [int(yk * L_eff) for yk in self.y_leftbounds]

        cells_int = {}
        for (xk, yk), ((lx, ox), (ly, oy)) in self.cells.items():
            xk_i = int(xk * L_eff)
            yk_i = int(yk * L_eff)
            lx_i = int(lx * L_eff)
            ox_i = int(ox * L_eff)
            ly_i = int(ly * L_eff)
            oy_i = int(oy * L_eff)
            cells_int[(xk_i, yk_i)] = (
                (lx_i, ox_i),
                (ly_i, oy_i)
            )

        # 5) Başlangıç X,Y
        X = int(x_r * L_eff)
        Y = int(y_r * L_eff)

        # optional viz setup
        self.vis_grid_shape = (len(x_bounds), len(y_bounds))
        self.vis_visited = []

        if verbose or utm:
            print('[INFO] Initial tape:')
            a = self.encoder.decode_alpha(x_r, 4)
            b = self.encoder.decode_beta(y_r, 24)
            print(''.join(a[::-1]) + ' . ' + ''.join(b))

        for step in tqdm(range(max_steps)):
            # 6) Bulunduğunuz hücre
            i = bisect_right(x_bounds, X) - 1
            j = bisect_right(y_bounds, Y) - 1
            self.vis_visited.append((i, j))

            # rasyonel anahtarlar
            x_key = self.x_leftbounds[i]
            y_key = self.y_leftbounds[j]

            # UTM‐halt kontrolünü rasyonel anahtarlarla yap
            if utm:
                state = self.encoder.decode_alpha(x_key, 0)[0]
                if state == 'CP_CLN':
                    buff = self.encoder.decode_beta(y_key, 200)
                    if 'X' in buff:
                        est = ''.join(buff[buff.index('X')+1:]).split('0')[0]
                        if est == encoded_utm_halting_state:
                            self.final_cell = (x_key, y_key)
                            print(f"[HALT] Accept state reached at step {step}")
                            self.decode_tm_tape()
                            break

            # integer key
            key_int = (x_bounds[i], y_bounds[j])
            if key_int not in cells_int:
                print(f"[WARN] No cell for key {key_int} at step {step}")
                break

            # 7) integer katsayılar
            (lx_i, ox_i), (ly_i, oy_i) = cells_int[key_int]

            # 8) güncelleme
            X = lx_i * X + ox_i
            Y = ly_i * Y + oy_i

            # final_cell’i rasyonel olarak güncelle (decode için)
            x_new_r = Rational(X, L_eff)
            y_new_r = Rational(Y, L_eff)
            self.final_cell = (x_new_r, y_new_r)

            # non-UTM accept check
            if not utm and key_int in getattr(self, 'accept_cells_int', ()):
                print(f"[HALT] Accept state reached at step {step}")
                self.decode_tm_tape()
                break

            if verbose:
                print(f"Step {step:3d}: x={fmt_frac(x_new_r,6)}, y={fmt_frac(y_new_r,6)}")

        print("Fixed-point sim OK!")

    
    def add_cell(self, left_dod, right_dod, left_affine, right_affine):
        """Gödelize edilerek hücreye karşılık gelen affine dönüşümler eklenir."""
        x = self.encoder.encode_alpha(left_dod[::-1])  # α′
        y = self.encoder.encode_beta(right_dod) # β
    
        # Hücre kaydı
        self.cells[(x, y)] = (left_affine, right_affine)
    
        # Bound listelerine sadece benzersiz değerleri ekle
        if x not in self.x_leftbounds:
            self.x_leftbounds.append(x)
        if y not in self.y_leftbounds:
            self.y_leftbounds.append(y)
    
        return x, y
    
    def check_cell(self, x: Rational, y: Rational) -> tuple[Rational, Rational]:
        """
        x, y : Rational
        Returns the left‐bound keys (x_key, y_key) for the cell containing (x,y).
        """
        # Find insertion points (bisect_right uses __lt__)
        i = bisect_right(self.x_leftbounds, x) - 1
        j = bisect_right(self.y_leftbounds, y) - 1
        
        return self.x_leftbounds[i], self.y_leftbounds[j]


    def build_from_transitions(self):
        gamma_q = self.encoder.gamma_q
        gamma_s = self.encoder.gamma_s
        nq = self.encoder.nq      # Rational
        ns = self.encoder.ns      # Rational
    
        # Rational helper constants
        one    = Rational(1)
        inv_nq = one / nq
        inv_ns = one / ns
        inv_nq2 = inv_nq ** 2
        inv_ns2 = inv_ns ** 2
    
        for (q, s_read), (q_next, s_write, direction) in self.versatile_shift.transitions.items():
            for s_left in self.encoder.symbols:
                left_dod  = [s_left, q]
                right_dod = [s_read]
    
                if direction == 'R':
                    lambda_x = inv_ns
                    a_x = (
                        - Rational(gamma_q[q]) * inv_nq * inv_ns
                        + Rational(gamma_s[s_write]) * inv_nq * inv_ns
                        + Rational(gamma_q[q_next]) * inv_nq
                    )
                    lambda_y = ns
                    a_y      = - Rational(gamma_s[s_read])
    
                elif direction == 'L':
                    lambda_x = ns
                    a_x = (
                        - Rational(gamma_q[q]) * inv_nq * ns
                        - Rational(gamma_s[s_left]) * inv_nq
                        + Rational(gamma_q[q_next]) * inv_nq
                    )
                    lambda_y = inv_ns
                    a_y = (
                        - Rational(gamma_s[s_read]) * inv_ns2
                        + Rational(gamma_s[s_write]) * inv_ns2
                        + Rational(gamma_s[s_left]) * inv_ns
                    )
    
                elif direction == 'N':
                    lambda_x = one
                    a_x = ( -Rational(gamma_q[q]) + Rational(gamma_q[q_next]) ) * inv_nq
                    
                    lambda_y = one
                    a_y = ( -Rational(gamma_s[s_read]) + Rational(gamma_s[s_write]) ) * inv_ns
    
                else:
                    raise ValueError(f"Unsupported direction: {direction!r}")
    
                x, y = self.add_cell(
                    left_dod, right_dod,
                    (lambda_x, a_x),
                    (lambda_y, a_y)
                )
    
                if q_next == self.versatile_shift.accept_state:
                    self.accept_coords.append((x, y))
    
        print("\n[INFO] NDA build from transitions (rational-only): OK!")
    
    def mark_accept_cells(self):
        """Accept state'lere karşılık gelen hücreleri i,j olarak işaretle."""
        self.x_leftbounds = sorted(set(self.x_leftbounds))
        self.y_leftbounds = sorted(set(self.y_leftbounds))
    
        self.accept_cells = []
        for x, y in self.accept_coords:
            i, j = self.check_cell(x, y)
            self.accept_cells.append((i, j))
        
    def initialize(self, initial_state, initial_tape, buff_len):
        tape = (
            [self.versatile_shift.blank_symbol] * buff_len +
            [initial_state, '.'] +
            list(initial_tape) +
            [self.versatile_shift.blank_symbol] * buff_len
        )
        head_pos = tape.index('.')
    
        alpha_seq = tape[:head_pos][::-1]  # α′
        beta_seq = tape[head_pos + 1:] if head_pos + 1 < len(tape) else [self.versatile_shift.blank_symbol]
    
        x = self.encoder.encode_alpha(alpha_seq)
        y = self.encoder.encode_beta(beta_seq)
        return x, y

    def simulate(self, initial_state, initial_tape, max_steps=100, buff_len=10, verbose=True, utm=False, encoded_utm_halting_state=None):
        self.vis_grid_shape = (len(self.x_leftbounds), len(self.y_leftbounds))
        self.vis_visited = []
        
        x, y = self.initialize(initial_state, initial_tape, buff_len)
            
        print('[INFO] Initial tape:')
        a = self.encoder.decode_alpha(x, 4)
        b = self.encoder.decode_beta(y, 24)
        print(''.join(a[::-1]) + ' . ' + ''.join(b))
    
        for step in tqdm(range(max_steps)):
            current_state = self.encoder.decode_alpha(x, 0)[0]       
            
            if utm and current_state == 'CP_CLN':
                buff = self.encoder.decode_beta(y, 200)
                if 'X' in buff:
                    encoded_estimated_state = ''.join(buff[buff.index('X')+1:]).split('0')[0]
                    if encoded_estimated_state == encoded_utm_halting_state:
                        print(f"[HALT] Accept state reached at step {step}")
                        self.decode_tm_tape()
                        break
            
            i, j = self.check_cell(x, y)
            if (i, j) not in self.cells:
                print(f"[WARN] No cell found for ({i}, {j}) at step {step}")
                break
                        
            vis_i = self.x_leftbounds.index(i)
            vis_j = self.y_leftbounds.index(j)
            self.vis_visited.append((vis_i, vis_j))
            
            (lambda_x, a_x), (lambda_y, a_y) = self.cells[(i, j)]
            
            if lambda_x * x + a_x < 0 or lambda_y * y + a_y < 0:
                pass
            
            x_new = lambda_x * x + a_x 
            y_new = lambda_y * y + a_y
            
            self.final_cell = (x_new, y_new)
            
            if not utm and (i, j) in self.accept_cells:
                print(f"[HALT] Accept state reached at step {step}")
                self.decode_tm_tape()
                break
            
            if verbose:
                print(f"Step {step:3d}: x={fmt_frac(x,6)}, y={fmt_frac(y,6)}")
                # self.decode_tm_tape(10,200)
    
            x, y = x_new, y_new
    
        print("Sim OK!")
        
    def decode_xy(self, x, y):
        a = self.encoder.decode_alpha(x, 4)
        b = self.encoder.decode_beta(y, 24)
        print(''.join(a[::-1]) + ' . ' + ''.join(b))
        
    def decode_tm_tape(self, sx=4, sy=24):
        a = self.encoder.decode_alpha(self.final_cell[0], sx)
        b = self.encoder.decode_beta(self.final_cell[1], sy)
        print(''.join(a[::-1]) + ' . ' + ''.join(b))
        return ''.join(a[::-1]) + ' . ' + ''.join(b)


#%%
class TMNonlinearDynamicalAutomatonShiftAdd:
    def __init__(self, encoder, versatile_shift):
        self.encoder = encoder
        self.versatile_shift = versatile_shift
        self.cells = {}
        self.x_leftbounds = []
        self.y_leftbounds = []
        self.accept_coords = []
        self.build_from_transitions()
        self.mark_accept_cells()
        self.x_leftbounds.sort()
        self.y_leftbounds.sort()

    def add_cell(self, left_dod, right_dod, left_affine, right_affine):
        x = self.encoder.encode_alpha(left_dod[::-1])
        y = self.encoder.encode_beta(right_dod)
        (lx, ax), (ly, ay) = left_affine, right_affine
        shift_x, off_x = dyadic_params(Fraction(lx), Fraction(ax))
        shift_y, off_y = dyadic_params(Fraction(ly), Fraction(ay))
        self.cells[(x, y)] = ((shift_x, off_x), (shift_y, off_y))
        if x not in self.x_leftbounds: self.x_leftbounds.append(x)
        if y not in self.y_leftbounds: self.y_leftbounds.append(y)
        return x, y

    def check_cell(self, x, y):
        i = bisect_right(self.x_leftbounds, x) - 1
        j = bisect_right(self.y_leftbounds, y) - 1
        return self.x_leftbounds[i], self.y_leftbounds[j]

    def build_from_transitions(self):
        gq = self.encoder.gamma_q
        gs = self.encoder.gamma_s
        nq, ns = len(gq), len(gs)
        inv_nq, inv_ns = Fraction(1, nq), Fraction(1, ns)
        for (q, s_read), (q_next, s_write, direction) in self.versatile_shift.transitions.items():
            for s_left in gs:
                left_dod  = [s_left, q]
                right_dod = [s_read]
                if direction == 'R':
                    lx, ax = inv_ns, (-gq[q]*inv_nq*inv_ns + gs[s_write]*inv_nq*inv_ns + gq[q_next]*inv_nq)
                    ly, ay = ns, -gs[s_read]
                elif direction == 'L':
                    lx, ax = ns, (-gq[q]*inv_nq*ns - gs[s_left]*inv_nq + gq[q_next]*inv_nq)
                    ly, ay = inv_ns, (-gs[s_read]*inv_ns*inv_ns + gs[s_write]*inv_ns*inv_ns + gs[s_left]*inv_ns)
                else:  # 'N'
                    lx, ax = 1, (-gq[q] + gq[q_next])*inv_nq
                    ly, ay = 1, (-gs[s_read] + gs[s_write])*inv_ns
                x, y = self.add_cell(left_dod, right_dod, (lx, ax), (ly, ay))
                if q_next == self.versatile_shift.accept_state:
                    self.accept_coords.append((x, y))

    def mark_accept_cells(self):
        self.x_leftbounds = sorted(set(self.x_leftbounds))
        self.y_leftbounds = sorted(set(self.y_leftbounds))
        self.accept_cells = [self.check_cell(x, y) for x, y in self.accept_coords]

    def initialize(self, initial_state, initial_tape, buff_len):
        tape = ([self.versatile_shift.blank_symbol]*buff_len + [initial_state, '.'] + list(initial_tape) + [self.versatile_shift.blank_symbol]*buff_len)
        head = tape.index('.')
        alpha = tape[:head][::-1]
        beta  = tape[head+1:] if head+1 < len(tape) else [self.versatile_shift.blank_symbol]
        return self.encoder.encode_alpha(alpha), self.encoder.encode_beta(beta)

    def simulate(self, initial_state, initial_tape, max_steps=100, buff_len=10, verbose=True, utm=False, encoded_utm_halting_state=None):
        self.vis_grid_shape = (len(self.x_leftbounds), len(self.y_leftbounds))
        self.vis_visited = []
        x, y = self.initialize(initial_state, initial_tape, buff_len)
        print('[INFO] Initial tape:')
        a = self.encoder.decode_alpha(x)
        b = self.encoder.decode_beta(y)
        print(''.join(a[::-1]) + ' . ' + ''.join(b))
        for step in tqdm(range(max_steps)):
            # find current cell
            cell_x, cell_y = self.check_cell(x, y)
            # UTM halt on cell coordinates
            if utm and self.encoder.decode_alpha(cell_x)[0] == 'CP_CLN':
                buff = self.encoder.decode_beta(cell_y)
                if 'X' in buff:
                    est = ''.join(buff[buff.index('X')+1:]).split('0')[0]
                    if est == encoded_utm_halting_state:
                        print(f"[HALT] Accept at step {step}")
                        self.decode_tm_tape()
                        break

            # check validity and track
            i, j = cell_x, cell_y
            if (i, j) not in self.cells:
                print(f"[WARN] No cell for ({i},{j}) at step {step}")
                break
            self.vis_visited.append((i, j))

            # affine shift-add update
            (sx, ox), (sy, oy) = self.cells[(i, j)]
            x = (x << sx) if sx > 0 else (x >> -sx)
            x += ox
            y = (y << sy) if sy > 0 else (y >> -sy)
            y += oy
            self.final_cell = (x, y)

            # accept check
            if not utm and (i, j) in self.accept_cells:
                print(f"[HALT] Accept at step {step}")
                self.decode_tm_tape()
                break

            if verbose:
                print(f"Step {step:3d}: x={x}, y={y}")

        print("Sim OK!")

    def decode_tm_tape(self, sx=4, sy=24):
        a = self.encoder.decode_alpha(self.final_cell[0])
        b = self.encoder.decode_beta(self.final_cell[1])
        print(''.join(a[::-1]) + ' . ' + ''.join(b))
        return ''.join(a[::-1]) + ' . ' + ''.join(b)





#%%
def create_transition_animation(visited, grid_shape, filename='transitions_sliding.gif',
                                    max_window=6, pixel_size=10, border_size=1, fps=10):
    """
    Create a GIF showing a sliding window of the last `max_window` visited cells.
    As new cells are visited beyond the window, the oldest in the window is dropped.
    Colors encode recency: viridis gradient for older to newest, with the newest in black.
    """
    frames = []
    n_total = len(visited)

    for step_idx in range(n_total):
        # Determine sliding window
        window = visited[max(0, step_idx - max_window + 1): step_idx + 1]
        win_len = len(window)

        # Build colormap for this frame
        cmap_vals = plt.cm.viridis(np.linspace(0, 1, win_len))
        cmap_vals[-1] = [0, 0, 0, 1]  # newest cell black
        cmap = colors.ListedColormap(cmap_vals)
        norm = colors.BoundaryNorm(np.arange(win_len+1)-0.5, win_len)

        # Build grid image
        grid = np.zeros(grid_shape, dtype=int)
        for idx, (i, j) in enumerate(window):
            grid[i, j] = idx + 1

        # Upsample to pixel_size
        img = np.kron(grid, np.ones((pixel_size, pixel_size)))

        # Add border
        h, w = img.shape
        framed = np.zeros((h + 2*border_size, w + 2*border_size), dtype=int)
        framed[border_size:border_size+h, border_size:border_size+w] = img

        # Plot
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.imshow(framed.T, cmap=cmap, norm=norm, origin='lower')
        ax.set_title(f"Step {step_idx}")
        ax.axis('off')

        # Capture frame
        fig.canvas.draw()
        buf = fig.canvas.tostring_rgb()
        height, width = fig.canvas.get_width_height()
        frame = np.frombuffer(buf, dtype='uint8').reshape((height, width, 3))
        frames.append(frame)
        plt.close(fig)

    # Save GIF
    imageio.mimsave(filename, frames, fps=fps)