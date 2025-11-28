# Present Outline

## Introduction

What is quantum error correction, and how to evaluate whether a quantum error correction code is good?
What is the surface code?


## Encoding
totalizer encoding for cardinality constraints
tree encoding for XOR

To verify whether a code can correct a given number of errors, we solve an UNSAT problem.
To verify whether a code cannot correct a given number of errors, we solve a SAT problem.


## Results

We successfully identified and verified a bug in a recently published Nature paper.

    | Distance | Actual # of errors can be corrected | What they claimed |
    | -------- | ----------------------------------- | ----------------- |
    | 3        | 0                                   | 0                 |
    | 5        | 1                                   | 1                 |
    | 7        | 2                                   | 2                 |
    | 9        | 3                                   | 3                 |
    | 11       | 3                                   | 4                 |
    | 13       | 4                                   | 5                 |

Some runtime results (pretty fast)
## Challenges
We can propose a fix for the bug, but we won't be able to verify whether it works.

Some runtime results (very slow)

Because it is a combination of several things that SAT solvers are not good at.

1. UNSAT problems
2. XOR encodings
3. Cardinality constraints
4. Pigeonhole principle

## Conclusion and Future Work

Use SAT to quickly prune the search space.
And use Lean to verify the correctness.