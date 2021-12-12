# AFLTeam: Towards Systematic and Dynamic Task Allocation for Collaborative Parallel Fuzzing

Parallel coverage-guided greybox fuzzing is the most common setup for vulnerability discovery at scale.
However, so far it has received little attention from the research community
compared to single-mode fuzzing, leaving open several problems particularly in
its task allocation strategies. Current approaches focus on managing micro tasks, at the seed input level, and
their task division algorithms are either ad-hoc or static. In our framework, we leverage research on graph partitioning and search
algorithms to propose a systematic and dynamic task allocation solution that works at the macro-task level.
First, we design an attributed graph to capture both the program structures
(e.g., program call graph) and fuzzing information (e.g., branch coverage).
Second, our graph partitioning algorithm divides the global program search space into sub-search-spaces.
Finally our search algorithm prioritizes these sub-search-spaces (i.e., tasks) and
explores them to maximize code coverage and number of bugs found.

# Tutorial - Fuzzing LibPNG with AFLTeam (Tested on Ubuntu 18.04 64-bit LLVM/Clang 6.0)

Please follow the steps below to fuzz LibPNG with AFLTeam. The same steps can be followed to run experiments
for other libraries/programs like LibJPEG-turbo, FFmpeg, and Jasper. The steps work for the following folder structure.

# Folder structure
```
<Your working folder>:
├── afl: normal AFL fuzzer (revision 518e422)
├── horsefuzz: a task-aware fuzzer built on top of AFL
├── aflsmart: we use seed corpora from AFLSmart
├── aflteam:
│   └── experiments
│   │   └── Makefile: for installing subject programs (LibPNG, FFMPEG etc)
|   └── aflteam-manager.py: the main script to run AFLTeam
|   └── setup-env.sh: for setting environment variables
├── subjects: we keep all subject programs in this folder
├── results: we keep all results in this folder
```

## Step-1. Set up required packages, AFLTeam, other fuzzers and environmental variables

Set up required packages and AFLTeam
```bash
git clone https://github.com/melbournefuzzinghub/aflteam aflteam
source aflteam/setup-env.sh $(pwd)
make -f $AFLTEAM/experiments/Makefile prerequisites
```

Set up other fuzzers
```bash
cd $WORKDIR
make -f $AFLTEAM/experiments/Makefile afl
make -f $AFLTEAM/experiments/Makefile aflsmart
make -f $AFLTEAM/experiments/Makefile horsefuzz
```

Create folders keeping subject programs and results
```bash
cd $WORKDIR
mkdir subjects
mkdir results
```

## Step-2. Set up subject program -- LibPNG in this example
```bash
cd $WORKDIR/subjects
make -f $AFLTEAM/experiments/Makefile libpng-all
```

## Step-3. Run experiments

Then run the following commands. Please check the aflteam-manager.py file to see the detailed argument list
```bash
cd $WORKDIR
mkdir $RESULTS/out-pngimage-aflteam
cp -r $SUBJECTS/libpng-horsefuzz/pngimage-horsefuzz-logs /tmp/pngimage
HF_BINARY=pngimage $AFLTEAM/aflteam-manager.py -bn pngimage -ab $SUBJECTS/libpng-afl/pngimage -hb $SUBJECTS/libpng-horsefuzz/pngimage -pb $SUBJECTS/libpng-horsefuzz-profiling/pngimage -gb $SUBJECTS/libpng-cov/pngimage -gf $SUBJECTS/libpng-cov -d $SUBJECTS/libpng-wllvm/pngimage.dot -i $AFLSMART/testcases/aflsmart/png -x $AFLSMART/dictionaries/png.dict -f /tmp/pngimage/func_ids.log -b /tmp/pngimage/func_bbs.log -c 10 -o $RESULTS/out-pngimage-aflteam -a lukes -tt 36000 -st 3600 -et 3600 -ea1 "" -ea2 ""
```
