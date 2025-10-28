"""
Utility functions for encoding constraints in SAT/MaxSAT problems.
Includes DEM file parsing, XOR encoding, and cardinality constraints.
"""

import re
from pysat.card import CardEnc


def parse_dem_file(dem_path: str):
    """
    Parse a DEM (Detector Error Model) file and extract error information.

    Returns:
        tuple: (num_errors, num_detectors, num_observables, error_effects)
        where error_effects is a list of tuples (detector_ids, observable_ids)
    """
    error_effects = []
    num_detectors = 0
    num_observables = 0

    with open(dem_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Parse error lines: error(prob) D0 D1 L0 or error[TYPE](prob) D0 D1
            if line.startswith("error"):
                # Extract targets (D# for detectors, L# for observables)
                # Split by space and find all D# and L# tokens
                parts = line.split()
                detector_ids = []
                observable_ids = []

                for part in parts[1:]:  # Skip the error(...) part
                    if part.startswith("D"):
                        det_id = int(part[1:])
                        detector_ids.append(det_id)
                        num_detectors = max(num_detectors, det_id + 1)
                    elif part.startswith("L"):
                        obs_id = int(part[1:])
                        observable_ids.append(obs_id)
                        num_observables = max(num_observables, obs_id + 1)

                error_effects.append((detector_ids, observable_ids))

            # Parse detector definition lines to get accurate count
            elif line.startswith("detector"):
                match = re.search(r"D(\d+)", line)
                if match:
                    det_id = int(match.group(1))
                    num_detectors = max(num_detectors, det_id + 1)

            # Parse logical observable definition lines
            elif line.startswith("logical_observable"):
                match = re.search(r"L(\d+)", line)
                if match:
                    obs_id = int(match.group(1))
                    num_observables = max(num_observables, obs_id + 1)

    num_errors = len(error_effects)
    return num_errors, num_detectors, num_observables, error_effects


def encode_xor_false(wcnf, vars, next_var):
    """
    Encode XOR(vars) = False using Tseitin transformation for WCNF.

    Args:
        wcnf: WCNF formula to add clauses to
        vars: List of variable IDs
        next_var: Next available variable ID

    Returns:
        int: The next available variable ID after encoding
    """
    if len(vars) == 0:
        return next_var
    if len(vars) == 1:
        wcnf.append([-vars[0]])
        return next_var

    # For XOR chain: x1 XOR x2 XOR ... XOR xn = False
    # Use auxiliary variables
    aux_vars = list(range(next_var, next_var + len(vars) - 1))

    # aux[0] = x1 XOR x2
    _encode_xor_binary(wcnf, vars[0], vars[1], aux_vars[0])

    # aux[i] = aux[i-1] XOR x[i+2]
    for i in range(1, len(aux_vars)):
        _encode_xor_binary(wcnf, aux_vars[i - 1], vars[i + 1], aux_vars[i])

    # Final result should be False
    wcnf.append([-aux_vars[-1]])

    return next_var + len(vars) - 1


def _encode_xor_binary(wcnf, a, b, c):
    """
    Encode c = a XOR b using CNF clauses for WCNF.

    Args:
        wcnf: WCNF formula to add clauses to
        a: First variable ID
        b: Second variable ID
        c: Result variable ID (c = a XOR b)
    """
    # c = a XOR b is equivalent to:
    # c <=> (a AND NOT b) OR (NOT a AND b)
    wcnf.append([-a, -b, -c])  # NOT (a AND b AND c)
    wcnf.append([a, b, -c])  # (a OR b) => c is false when both true
    wcnf.append([a, -b, c])  # a AND NOT b => c
    wcnf.append([-a, b, c])  # NOT a AND b => c


def add_cardinality_constraint(solver, variables, max_count, next_var):
    """
    Add constraint that at most max_count of the variables can be true.
    Uses pysat's CardEnc with totalizer encoding.

    This function is compatible with pycryptosat Solver objects.

    Args:
        solver: Solver object with add_clause method
        variables: List of variable IDs
        max_count: Maximum number of variables that can be true
        next_var: Next available variable ID

    Returns:
        int: The next available variable ID after encoding
    """
    n = len(variables)
    if max_count >= n:
        return next_var

    # Use pysat's CardEnc to generate at-most-k constraint
    # encoding=6 is totalizer encoding (good balance of size and propagation)
    cnf = CardEnc.atmost(
        lits=variables, bound=max_count, top_id=next_var - 1, encoding=6
    )

    # Add all generated clauses to the solver
    for clause in cnf.clauses:
        solver.add_clause(clause)

    # Update next_var based on auxiliary variables used by CardEnc
    # cnf.nv is the highest variable ID used
    return cnf.nv + 1


def add_cardinality_constraint_wcnf(wcnf, variables, max_count, next_var):
    """
    Add constraint that at most max_count of the variables can be true.
    Uses pysat's CardEnc with totalizer encoding for WCNF formulas.

    Args:
        wcnf: WCNF formula to add clauses to
        variables: List of variable IDs
        max_count: Maximum number of variables that can be true
        next_var: Next available variable ID

    Returns:
        int: The next available variable ID after encoding
    """
    n = len(variables)
    if max_count >= n:
        return next_var

    # Use pysat's CardEnc to generate at-most-k constraint
    cnf = CardEnc.atmost(
        lits=variables, bound=max_count, top_id=next_var - 1, encoding=6
    )

    # Add all generated clauses to the WCNF
    for clause in cnf.clauses:
        wcnf.append(clause)

    # Update next_var based on auxiliary variables used by CardEnc
    return cnf.nv + 1
