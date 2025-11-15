"""
CaDiCaL SAT solver implementation for surface code verification.
CaDiCaL is a high-performance SAT solver accessed through PySAT.
"""

from pysat.solvers import Cadical195
from encoding_utils import parse_dem_file, add_cardinality_constraint

def encode_xor_false_cadical_bruteforce(solver, vars):
    """
    Encode XOR(vars) = False using brute force for CaDiCaL.

    Args:
        solver: CaDiCaL solver object
        vars: List of variable IDs
    """
    n = len(vars)

    # Iterate over all 2^n assignments
    for mask in range(1 << n):
        # count ones (True assignments)
        ones = bin(mask).count("1")
        parity = ones % 2

        # If parity is odd (i.e., XOR = True), forbid this assignment
        if parity == 1:
            solver.add_clause([-v if (mask >> i) & 1 == 1 else v for i, v in enumerate(vars)])
    return


def encode_xor_false_cadical_tseitin(solver, vars):
    """
    Encode XOR(vars) = False using Tseitin transformation for CaDiCaL.

    Args:
        solver: CaDiCaL solver object
        vars: List of variable IDs
    """
    if len(vars) == 0:
        return
    if len(vars) == 1:
        solver.add_clause([-vars[0]])
        return
    
    # For XOR chain: x1 XOR x2 XOR ... XOR xn = False
    # Use auxiliary variables
    next_var = solver.nof_vars() + 1
    aux_vars = list(range(next_var, next_var + len(vars) - 1))

    # aux[0] = x1 XOR x2
    _encode_xor_binary_cadical(solver, vars[0], vars[1], aux_vars[0])

    # aux[i] = aux[i-1] XOR x[i+2]
    for i in range(1, len(aux_vars)):
        _encode_xor_binary_cadical(solver, aux_vars[i - 1], vars[i + 1], aux_vars[i])

    # Final result should be False
    solver.add_clause([-aux_vars[-1]])
    # ! try some other encoding, for example, a complete tree instead of a chain
    # ! brute force when len(vars) <= 4/
    # ! https://github.com/jreeves3/Cardinality-CDCL


def _encode_xor_binary_cadical(solver, a, b, c):
    """
    Encode c = a XOR b using CNF clauses for CaDiCaL.

    Args:
        solver: CaDiCaL solver object
        a: First variable ID
        b: Second variable ID
        c: Result variable ID (c = a XOR b)
    """
    # c = a XOR b is equivalent to:
    # c <=> (a AND NOT b) OR (NOT a AND b)
    solver.add_clause([-a, -b, -c])  # NOT (a AND b AND c)
    solver.add_clause([a, b, -c])  # (a OR b) => c is false when both true
    solver.add_clause([a, -b, c])  # a AND NOT b => c
    solver.add_clause([-a, b, c])  # NOT a AND b => c


def encode_xor_false_cadical_tree(solver, vars):
    """
    Encode XOR(vars) = False using a tree-based Tseitin transformation for CaDiCaL.

    Args:
        solver: CaDiCaL solver object
        vars:   List of variable IDs (positive integers)
    """
    vars = list(vars)
    if len(vars) == 0:
        return

    if len(vars) == 1:
        solver.add_clause([-vars[0]])
        return

    # We'll build a balanced XOR tree:
    #  - At each level, pair up variables and introduce an aux var c = a XOR b.
    #  - If there's an odd one out, just carry it up unchanged.
    #  - The final single variable t at the root satisfies t = XOR(vars).
    #  - Then enforce t = False.

    next_var = solver.nof_vars() + 1

    def new_var():
        nonlocal next_var
        v = next_var
        next_var += 1
        return v

    current = vars
    while len(current) > 1:
        next_level = []
        i = 0
        n = len(current)
        while i < n:
            if i + 1 < n:
                a = current[i]
                b = current[i + 1]
                c = new_var()
                # c == a XOR b
                _encode_xor_binary_cadical(solver, a, b, c)
                next_level.append(c)
                i += 2
            else:
                # Odd number of nodes: pass the last one up unchanged
                next_level.append(current[i])
                i += 1
        current = next_level

    # Root of the tree: t = XOR(original vars)
    t = current[0]

    # Enforce XOR(vars) = False  <=> t = False
    solver.add_clause([-t])


def encode_xor_false_cadical(solver, vars, method):
    """
    Encode XOR(vars) = False for CaDiCaL.

    Args:
        solver: CaDiCaL solver object
        vars: List of variable IDs

    """

    if len(vars) <= 3:
        encode_xor_false_cadical_bruteforce(solver, vars)
    elif method == "chain_tseitin":
        encode_xor_false_cadical_tseitin(solver, vars)
    elif method == "tree_tseitin":
        encode_xor_false_cadical_tree(solver, vars)


def build_verification_model(dem_path: str, max_errors: int, xor_encoding_method="chain_tseitin"):
    """
    Build SAT model from a DEM file to verify if there exists
    an error pattern that:
    - Triggers no detectors (all detectors have even parity)
    - Triggers at least one logical observable (at least one has odd parity)
    - Uses at most max_errors error mechanisms
    """
    # Parse DEM file
    (
        num_errors,
        num_detectors,
        num_observables,
        error_effects_list,
        detectors_by_x_coord,
    ) = parse_dem_file(dem_path)

    solver = Cadical195()

    # Create boolean variable for each error mechanism
    error_vars = list(range(1, num_errors + 1))

    # Reserve variables for error mechanisms
    for var in error_vars:
        solver.add_clause([var, -var])  # Dummy clause to register variable

    # Build detector and logical constraints
    # Each detector/logical = XOR of errors affecting it
    detector_effects = [[] for _ in range(num_detectors)]
    logical_effects = [[] for _ in range(num_observables)]

    # Populate effects from parsed data
    for error_idx, (detector_ids, observable_ids) in enumerate(error_effects_list):
        error_var = error_vars[error_idx]

        # Add this error to all detectors it affects
        for det_id in detector_ids:
            detector_effects[det_id].append(error_var)

        # Add this error to all observables it affects
        for obs_id in observable_ids:
            logical_effects[obs_id].append(error_var)

    # Constraint: all detectors must not be triggered (XOR = 0)
    for det_id in range(num_detectors):
        if detector_effects[det_id]:
            # Encode XOR = False using Tseitin transformation
            encode_xor_false_cadical(solver, detector_effects[det_id], xor_encoding_method)

    # Constraint: at least one logical observable must be triggered (XOR = 1)
    # Create auxiliary variables for each observable's XOR result
    logical_result_vars = []
    for obs_id in range(num_observables):
        if logical_effects[obs_id]:
            # Get next available variable
            obs_result_var = solver.nof_vars() + 1
            logical_result_vars.append(obs_result_var)

            _vars = logical_effects[obs_id] + [obs_result_var]
            encode_xor_false_cadical(solver, _vars, xor_encoding_method)

    # At least one logical observable must be triggered
    if logical_result_vars:
        solver.add_clause(logical_result_vars)

    # Group errors by x-coordinate combination of their affected detectors
    # Only consider two types of errors:
    # 1. Errors affecting 2 detectors with different x-coordinates (cross-column)
    # 2. Errors affecting only 1 detector (boundary errors)
    errors_by_x_coords = {}  # key: tuple of sorted x-coordinates
    for error_idx, (detector_ids, observable_ids) in enumerate(error_effects_list):
        error_var = error_vars[error_idx]

        # Find x-coordinates of detectors this error affects
        x_coords = set()
        for det_id in detector_ids:
            # Find which x-coordinate this detector belongs to
            for x_coord, det_list in detectors_by_x_coord.items():
                if det_id in det_list:
                    x_coords.add(x_coord)

        # Only include errors with 1 detector OR 2 detectors with different x-coords
        if len(x_coords) == 1 or len(x_coords) == 2:
            # Skip if 2 detectors but same x-coordinate (vertical errors)
            if len(detector_ids) == 2 and len(x_coords) == 1:
                continue

            # Classify this error by its x-coordinate combination
            x_coords_key = tuple(sorted(x_coords))
            if x_coords_key not in errors_by_x_coords:
                errors_by_x_coords[x_coords_key] = []
            errors_by_x_coords[x_coords_key].append(error_var)

    # Add connectivity constraints for each logical observable
    # If a logical is triggered, at least one error from each category must be active
    if logical_result_vars:
        for logical_var in logical_result_vars:
            print(f"Number of error categories: {len(errors_by_x_coords.keys())}")
            for x_coords_key in sorted(errors_by_x_coords.keys()):
                if errors_by_x_coords[x_coords_key]:
                    # logical_var → (at least one error in this category)
                    # ¬logical_var ∨ (e1 ∨ e2 ∨ ... ∨ en)
                    clause = [-logical_var] + errors_by_x_coords[x_coords_key]
                    solver.add_clause(clause)

    # Add cardinality constraint
    next_var = solver.nof_vars() + 1
    add_cardinality_constraint(solver, error_vars, max_errors, next_var)

    return solver, error_vars, detector_effects, logical_effects


def get_dem_path(distance: int) -> str:
    """Return the path to the DEM file for the given distance."""
    return f"circuits/circuit_{distance}.dem"


if __name__ == "__main__":
    import time

    # for distance in [3, 5, 7, 9, 11]:
    for xor_encoding_method in ["chain_tseitin", "tree_tseitin"]:
        print(f"Testing XOR encoding method: {xor_encoding_method}")
        for distance in [3, 5, 7, 9]:
            for bias in [1, 0]:
                print("--------------------------------")
                print(f"Testing distance {distance} with bias {distance - bias} errors")
                dem_path = get_dem_path(distance)
                start_time = time.time()
                solver, error_vars, detector_effects, logical_effects = build_verification_model(
                    dem_path, distance - bias, xor_encoding_method
                )
                print(f"num vars: {solver.nof_vars()}")
                build_time = time.time() - start_time
                print(f"Build time: {build_time} seconds")
                start_time = time.time()
                sat = solver.solve()
                check_time = time.time() - start_time
                print(f"Check time: {check_time} seconds")
                if sat:
                    print(
                        f"A code with distance {distance} can't tolerate {distance - bias} loss errors"
                    )
                    # Optional: print solution
                    # model = solver.get_model()
                    # active_errors = [i for i, var in enumerate(error_vars, 1) if var in model]
                    # print(f"Active errors: {active_errors}")
                else:
                    print(
                        f"A code with distance {distance} can tolerate {distance - bias} loss errors"
                    )

                # Clean up
                solver.delete()
