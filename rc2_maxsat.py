# pyright: reportGeneralTypeIssues=false

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF
from encoding_utils import parse_dem_file, encode_xor_false


def build_maxsat_model(dem_path: str):
    """
    Build MaxSAT model to find minimum number of errors needed.

    Hard constraints:
    - All detectors not triggered (XOR = False)
    - At least one logical observable triggered (XOR = True)

    Soft constraints (weight=1 each):
    - Each error should not occur (¬error_i)

    Objective: Maximize errors NOT occurring = Minimize errors occurring
    """
    # Parse DEM file
    num_errors, num_detectors, num_observables, error_effects_list, detectors_by_x_coord = parse_dem_file(dem_path)

    wcnf = WCNF()

    # Create boolean variable for each error mechanism (1-indexed)
    error_vars = list(range(1, num_errors + 1))
    next_var = num_errors + 1

    # Build detector and logical constraints
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

    # HARD Constraint: all detectors must not be triggered (XOR = False)
    for det_id in range(num_detectors):
        if detector_effects[det_id]:
            next_var = encode_xor_false(wcnf, detector_effects[det_id], next_var)

    # HARD Constraint: at least one logical observable must be triggered (XOR = True)
    logical_result_vars = []
    for obs_id in range(num_observables):
        if logical_effects[obs_id]:
            obs_result_var = next_var
            next_var += 1
            logical_result_vars.append(obs_result_var)

            # XOR(e1, e2, ..., en) = obs_result_var
            # Encoded as: XOR(e1, e2, ..., en, obs_result_var) = False
            next_var = encode_xor_false(
                wcnf, logical_effects[obs_id] + [obs_result_var], next_var
            )

    # At least one logical observable must be triggered
    if logical_result_vars:
        wcnf.append(logical_result_vars)

    # SOFT Constraints: prefer errors to NOT occur
    # Each soft clause has weight 1
    for error_var in error_vars:
        wcnf.append([-error_var], weight=1)

    return wcnf, error_vars, next_var


def get_dem_path(distance: int) -> str:
    """Return the path to the DEM file for the given distance."""
    return f"circuits/circuit_{distance}.dem"


if __name__ == "__main__":
    import time

    for distance in [3, 5, 7, 9, 11]:
        print("=" * 60)
        print(f"Testing distance {distance}")
        dem_path = get_dem_path(distance)

        start_time = time.time()
        wcnf, error_vars, next_var = build_maxsat_model(dem_path)
        print(f"Total vars: {next_var - 1}")
        print(f"Num hard clauses: {len(wcnf.hard)}")
        print(f"Num soft clauses: {len(wcnf.soft)}")
        build_time = time.time() - start_time
        print(f"Build time: {build_time:.3f} seconds")

        start_time = time.time()
        solver = RC2(wcnf)
        model = solver.compute()
        check_time = time.time() - start_time
        print(f"Solve time: {check_time:.3f} seconds")

        if model:
            # Count how many errors occurred
            errors_triggered = [i for i in range(1, len(error_vars) + 1) if i in model]
            num_errors = len(errors_triggered)
            print(f"Minimum errors needed to cause logical failure: {num_errors}")
        else:
            raise ValueError("No solution found")

        print()
