This is the public repository for ASE'21 NIER paper entitled "Towards Systematic and Dynamic Task Allocation for Collaborative Parallel Fuzzing". The source code will be released by Nov 15th 2021.

# Towards Systematic and Dynamic Task Allocation for Collaborative Parallel Fuzzing

Parallel coverage-guided greybox fuzzing is the most common setup for vulnerability discovery at scale.
However, so far it has received little attention from the research community
compared to single-mode fuzzing, leaving open several problems particularly in
its task allocation strategies. Current approaches focus on managing micro tasks, at the seed input level, and
their task division algorithms are either ad-hoc or static. In our framework, we leverage research on graph partitioning and search
algorithms to propose a systematic and dynamic task allocation solution that works at the macro-task level.
First, we design an attributed graph to capture both the program structures
(e.g., program call graph) and fuzzing information (e.g., branch hit counts, bug discovery probability).
Second, our graph partitioning algorithm divides the global program search space into sub-search-spaces.
Finally our search algorithm prioritizes these sub-search-spaces (i.e., tasks) and
explores them to maximize code coverage and number of bugs found.

