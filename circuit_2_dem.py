import stim

for d in [3, 5, 7, 9, 11]:
    circuit = stim.Circuit.from_file(f"circuits/circuit_{d}.stim")
    with open(f"circuits/circuit_{d}.dem", "w") as f:
        f.write(str(circuit.detector_error_model()))
