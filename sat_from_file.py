from pycryptosat import Solver
from pysat.card import CardEnc
import re


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

    with open(dem_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Parse error lines: error(prob) D0 D1 L0 or error[TYPE](prob) D0 D1
            if line.startswith('error'):
                # Extract targets (D# for detectors, L# for observables)
                # Split by space and find all D# and L# tokens
                parts = line.split()
                detector_ids = []
                observable_ids = []

                for part in parts[1:]:  # Skip the error(...) part
                    if part.startswith('D'):
                        det_id = int(part[1:])
                        detector_ids.append(det_id)
                        num_detectors = max(num_detectors, det_id + 1)
                    elif part.startswith('L'):
                        obs_id = int(part[1:])
                        observable_ids.append(obs_id)
                        num_observables = max(num_observables, obs_id + 1)

                error_effects.append((detector_ids, observable_ids))

            # Parse detector definition lines to get accurate count
            elif line.startswith('detector'):
                match = re.search(r'D(\d+)', line)
                if match:
                    det_id = int(match.group(1))
                    num_detectors = max(num_detectors, det_id + 1)

            # Parse logical observable definition lines
            elif line.startswith('logical_observable'):
                match = re.search(r'L(\d+)', line)
                if match:
                    obs_id = int(match.group(1))
                    num_observables = max(num_observables, obs_id + 1)

    num_errors = len(error_effects)
    return num_errors, num_detectors, num_observables, error_effects


def add_cardinality_constraint(solver, variables, max_count, next_var):
    """
    Add constraint that at most max_count of the variables can be true.
    Uses pysat's CardEnc with sequential counter encoding.
    """
    n = len(variables)
    if max_count >= n:
        return next_var

    # Use pysat's CardEnc to generate at-most-k constraint
    # encoding=1 is EncType.seqcounter (sequential counter)
    cnf = CardEnc.atmost(
        lits=variables, bound=max_count, top_id=next_var - 1, encoding=6
    )

    # Add all generated clauses to the solver
    for clause in cnf.clauses:
        solver.add_clause(clause)

    # Update next_var based on auxiliary variables used by CardEnc
    # cnf.nv is the highest variable ID used
    return cnf.nv + 1


def build_verification_model(dem_path: str, max_errors: int):
    """
    Build SAT model from a DEM file to verify if there exists
    an error pattern that:
    - Triggers no detectors (all detectors have even parity)
    - Triggers at least one logical observable (at least one has odd parity)
    - Uses at most max_errors error mechanisms
    """
    # Parse DEM file
    num_errors, num_detectors, num_observables, error_effects_list = parse_dem_file(dem_path)

    solver = Solver()

    # Create boolean variable for each error mechanism (1-indexed in pycryptosat)
    error_vars = list(range(1, num_errors + 1))
    next_var = num_errors + 1

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
            # Use native XOR clause support: XOR(variables) = False means even parity
            solver.add_xor_clause(detector_effects[det_id], False)

    # Constraint: at least one logical observable must be triggered (XOR = 1)
    # Create auxiliary variables for each observable's XOR result
    logical_result_vars = []
    for obs_id in range(num_observables):
        if logical_effects[obs_id]:
            # Create auxiliary variable to represent this observable being triggered
            obs_result_var = next_var
            next_var += 1
            logical_result_vars.append(obs_result_var)

            # XOR(e1, e2, ..., en) = obs_result_var
            # Encoded as: XOR(e1, e2, ..., en, obs_result_var) = False
            solver.add_xor_clause(logical_effects[obs_id] + [obs_result_var], False)

    # At least one logical observable must be triggered
    if logical_result_vars:
        solver.add_clause(logical_result_vars)

    next_var = add_cardinality_constraint(solver, error_vars, max_errors, next_var)

    return solver, error_vars, detector_effects, logical_effects


def get_dem_path(distance: int) -> str:
    """Return the path to the DEM file for the given distance."""
    return f"circuits/circuit_{distance}.dem"


if __name__ == "__main__":
    import time

    for distance in [3, 5, 7, 9, 11]:
        for bias in [1, 0]:
            print("--------------------------------")
            print(f"Testing distance {distance} with bias {distance - bias} errors")
            dem_path = get_dem_path(distance)
            start_time = time.time()
            s, error_vars, detector_effects, logical_effects = build_verification_model(
                dem_path, distance - bias
            )
            print(f"num vars: {s.nb_vars()}")
            build_time = time.time() - start_time
            print(f"Build time: {build_time} seconds")
            start_time = time.time()
            sat, solution = s.solve()
            check_time = time.time() - start_time
            print(f"Check time: {check_time} seconds")
            if sat:
                print(
                    f"A code with distance {distance} can't tolerate {distance - bias} loss errors"
                )
            else:
                print(
                    f"A code with distance {distance} can tolerate {distance - bias} loss errors"
                )
