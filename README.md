# surface_code_sat

Installation:

```
uv sync
```

DEM (Detector Error Model) format:
```
error(0.02741843737473918) D0 D1 # each row corresponds to an error mechanism
error(0.1426666666666667) D0 D2 # D0 and D2 represents detector ids that the error mechanism affects.
error[LOSS_RESOLVING_READOUT](0.1) D0 L0 # L0 represents logical observable id.

```

Convert to SAT format:
+ Each row or error mechanism corresponds to a boolean variable.
+ For each detector, the xor of the boolean variables that the error mechanism affects must be 0.
+ For the logical observable, the xor of the boolean variables that the error mechanism affects must be 1.
+ Find the minimum number of error mechanisms set to true that all such constraints are satisfied.