# Surface Code SAT Solver

SAT/MaxSAT-based solver for analyzing quantum surface codes. Converts quantum error correction problems into boolean satisfiability to find minimum-weight logical errors and verify fault tolerance.

## Installation

```bash
uv sync
```

## DEM (Detector Error Model) Format

```
error(0.0274) D0 D1                    # Error affecting detectors D0, D1
error(0.1427) D0 D2                    # D# = detector IDs
error[LOSS_RESOLVING_READOUT](0.1) D0 L0  # L# = logical observable IDs
```

## SAT Encoding

1. Each error mechanism → boolean variable
2. For each detector: XOR of affecting errors = 0 (no syndrome)
3. For logical observable: XOR of affecting errors = 1 (logical error)
4. Minimize number of errors satisfying all constraints

## Solvers

- **z3_solver.py**: Z3 SMT solver (handles modular arithmetic naturally)
- **cryptominisat.py**: CryptoMiniSat (fast SAT with XOR support)
- **rc2_maxsat.py**: RC2 MaxSAT (no manual search needed)

XOR constraints use Tseitin transformation; cardinality constraints use built-in pysat encoding.