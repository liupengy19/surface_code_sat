# pyright: reportGeneralTypeIssues=false

from z3 import *
from encoding_utils import parse_dem_file


def build_verification_model(dem_path: str, max_errors: int):
    """
    Build Z3 model from a DEM file to verify if there exists
    an error pattern that:
    - Does not trigger any detectors (syndrome = 0)
    - Triggers the logical observable (logical error)
    - Uses at most max_errors error mechanisms
    """
    # Parse DEM file
    num_errors, num_detectors, num_observables, error_effects_list, detectors_by_x_coord = parse_dem_file(
        dem_path
    )

    s = Solver()

    # Create boolean variable for each error mechanism
    error_vars = [Bool(f"E_{i}") for i in range(num_errors)]

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
            xor_sum = Sum([If(e, 1, 0) for e in detector_effects[det_id]])
            s.add(xor_sum % 2 == 0)

    # Constraint: at least one logical observable must be triggered (XOR = 1)
    logical_conditions = []
    for obs_id in range(num_observables):
        if logical_effects[obs_id]:
            xor_sum = Sum([If(e, 1, 0) for e in logical_effects[obs_id]])
            logical_conditions.append(xor_sum % 2 == 1)

    s.add(Or(logical_conditions))

    # Optional: limit number of errors
    total_errors = Sum([If(e, 1, 0) for e in error_vars])
    s.add(total_errors <= max_errors)

    return s, error_vars, detector_effects, logical_effects


def get_dem_path(distance: int) -> str:
    """Return the path to the DEM file for the given distance."""
    return f"circuits/circuit_{distance}.dem"


if __name__ == "__main__":
    import sys
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
            build_time = time.time() - start_time
            print(f"Build time: {build_time} seconds")
            start_time = time.time()
            result = s.check()
            check_time = time.time() - start_time
            print(f"Check time: {check_time} seconds")
            if result == sat:
                print(
                    f"A code with distance {distance} can't tolerate {distance - bias} loss errors"
                )
            else:
                print(
                    f"A code with distance {distance} can tolerate {distance - bias} loss errors"
                )
