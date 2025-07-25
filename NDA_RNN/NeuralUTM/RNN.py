import numpy as np

# -----------------------------------------------------------------------------
# 1) NDA → R‐ANN mapper
# -----------------------------------------------------------------------------

class NDAtoRANN:
    def __init__(self, nda):
        """
        nda: object with attributes
          - x_leftbounds: list of m left‐interval endpoints on x
          - y_leftbounds: list of n left‐interval endpoints on y
          - cells: dict mapping (x_bound, y_bound) → ((λx, ax), (λy, ay))
          - accept_cells: set of (i,j) indices to halt on
        """
        self.nda = nda
        self.m = len(nda.x_leftbounds)
        self.n = len(nda.y_leftbounds)
        self._extract_affine()
        self._build_bsl2ltl()
        self._build_mcl2ltl()
        self._build_ltl_bias()
        self._build_ltl2mcl()

     def _extract_affine(self):
         m,n = self.m, self.n
-        self.x_params = np.zeros((m,n,2),dtype=float)
-        self.y_params = np.zeros((m,n,2),dtype=float)
+        self.x_params = np.zeros((m,n,2),dtype=float)
+        self.y_params = np.zeros((m,n,2),dtype=float)

         for (xk,yk),((lx,ax),(ly,ay)) in self.nda.cells.items():
             i = self.nda.x_leftbounds.index(xk)
             j = self.nda.y_leftbounds.index(yk)
-            self.x_params[i,j,0] = lx
-            self.x_params[i,j,1] = ax
-            self.y_params[i,j,0] = ly
-            self.y_params[i,j,1] = ay
+            # cast everything to Python float here:
+            self.x_params[i,j,0] = float(lx)
+            self.x_params[i,j,1] = float(ax)
+            self.y_params[i,j,0] = float(ly)
+            self.y_params[i,j,1] = float(ay)

         # compute inhibitory bias h
-        self.h = 2.0 * max(Mx, My)
+        self.h = float(2.0 * max(Mx, My))

    def _build_bsl2ltl(self):
        m,n,nb = self.m,self.n,self.n_branches
        h = self.h
        # BSL_x → LTL
        self.W_bslx_ltl = np.zeros((m, 2*nb), dtype=float)
        for col in range(m):
            # excitatory to branches with x‐index == col
            idxs = np.arange(nb)[col::m]
            self.W_bslx_ltl[col, :nb][idxs] +=  h/2
            if col>0:
                idxs_left = np.arange(nb)[col-1::m]
                self.W_bslx_ltl[col, :nb][idxs_left] += -h/2
        # BSL_y → LTL
        self.W_bsly_ltl = np.zeros((n, 2*nb), dtype=float)
        for row in range(n):
            idxs = np.arange(nb)[row*m : row*m + m]
            self.W_bsly_ltl[row, :nb][idxs] +=  h/2
            if row>0:
                idxs_up = np.arange(nb)[(row-1)*m:(row-1)*m + m]
                self.W_bsly_ltl[row, :nb][idxs_up] += -h/2

    def _build_mcl2ltl(self):
        nb = self.n_branches
        # MCL_x → LTL
        self.W_mclx_ltl = np.zeros((1, 2*nb), dtype=float)
        self.W_mclx_ltl[0, :nb]    = self.x_params[:,:,0].ravel()
        # MCL_y → LTL
        self.W_mcly_ltl = np.zeros((1, 2*nb), dtype=float)
        self.W_mcly_ltl[0, nb:]    = self.y_params[:,:,0].ravel()

    def _build_ltl_bias(self):
        nb = self.n_branches
        # biases = [ax,…,ax, ay,…,ay] - h
        b = np.zeros(2*nb, dtype=float)
        b[:nb]  = self.x_params[:,:,1].ravel()
        b[nb:]  = self.y_params[:,:,1].ravel()
        self.b_ltl = b - self.h

    def _build_ltl2mcl(self):
        nb = self.n_branches
        # sum all x‐branch activations
        self.W_ltl_mclx = np.zeros((2*nb,1),dtype=float)
        self.W_ltl_mclx[:nb,0] = 1.0
        # sum all y‐branch activations
        self.W_ltl_mcly = np.zeros((2*nb,1),dtype=float)
        self.W_ltl_mcly[nb:,0] = 1.0

    def simulate(self, init_x, init_y, max_steps=200, verbose=True):
        """Run the R‐ANN for up to max_steps or until an accept cell is reached."""
        x_lb = np.array(self.nda.x_leftbounds, dtype=float)
        y_lb = np.array(self.nda.y_leftbounds, dtype=float)
        m,n,nb = self.m,self.n,self.n_branches

        cx, cy = float(init_x), float(init_y)
        traj = [(cx, cy)]
        if verbose:
            print(" # |    cx     |    cy     | cell(i,j)")
            print(f" 0 | {cx: .6f} | {cy: .6f} |    - , -")

        for t in range(1, max_steps+1):
            # 1) BSL
            bx = (cx >= x_lb).astype(float)    # shape (m,)
            by = (cy >= y_lb).astype(float)    # shape (n,)

            # 2) LTL input from BSL
            B = bx @ self.W_bslx_ltl + by @ self.W_bsly_ltl  # (2*nb,)

            # 3) add MCL→LTL contributions + bias
            U = np.empty_like(B)
            U[:nb]  = cx * self.x_params[:,:,0].ravel() \
                      + self.x_params[:,:,1].ravel() + B[:nb] - self.h
            U[nb:]  = cy * self.y_params[:,:,0].ravel() \
                      + self.y_params[:,:,1].ravel() + B[nb:] - self.h

            # 4) Ramp activation and keep only _one_ global max per stream
            Tx = np.maximum(0, U[:nb])
            Ty = np.maximum(0, U[nb:])
            cx = Tx.argmax() >= 0 and Tx.max() or 0.0
            cy = Ty.argmax() >= 0 and Ty.max() or 0.0

            traj.append((cx, cy))

            # 5) check which NDA‐cell we landed in
            i,j = self.nda.check_cell(cx, cy)

            if verbose:
                print(f"{t:3d} | {cx: .6f} | {cy: .6f} | cell({i},{j})")

            if (i,j) in self.nda.accept_cells:
                print(f"[HALT] accept‐cell reached at step {t}")
                break

        return traj