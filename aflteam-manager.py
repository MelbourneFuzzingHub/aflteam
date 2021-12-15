#!/usr/bin/env python3

import re
import sys
import argparse
import os
import signal
import time
import copy
import networkx as nx
import operator
import subprocess
import psutil
from shutil import copyfile
import logging
import shutil
import math
from datetime import datetime

#import AFLTeam's modules
from utils import helpers
from utils import extractors
from graphs import networkx_processing as nxp
from tasks import lukes_partitioning as lukes
from tasks import dac_partitioning as dac
from monitors import stopping
import globals

'''
main loop of AFLTeam
'''

def main(binary_name, afl_binary, horsefuzz_binary, profiling_binary, gcov_binary, gcov_folder, pre_args, post_args, seed_corpus, out_folder, dict_file, dot_file, func_ids, func_bbs, cores, algorithm, total_timeout, scanning_timeout, expl_timeout):
  #Create a log file
  LOG_FILENAME = os.path.join(out_folder, "aflteam.log")
  logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
  logging.debug("AFLTeam starts")

  #Get the initial callgraph & related information
  #v_fname_dict: a dictionary to map from vertices to function names
  #fname_v_dict: a dictionary to map from function names to vertices
  #main_v: the root vertice
  
  (CG, v_fname_dict, fname_v_dict, main_v) = nxp.extract_callgraph(dot_file)
  
  #Get all functions and their corresponding source files based on
  #the func_ids.log file
  
  fname_src_dict = extractors.extract_fname_src_dict(func_ids)

  #Get all functions and their corresponding basic block count
  fname_bbs_dict = extractors.extract_fname_bbs_dict(func_bbs)

  #Prune callgraph to remove "uninteresting" functions
  nxp.prune_callgraph(CG, main_v, v_fname_dict, fname_v_dict, fname_bbs_dict)

  #Start the monitoring fuzzer which is always running
  activeDir = out_folder + "/active_runs"
  os.mkdir(activeDir)
  originalSeedDir = activeDir + "/seeds_origin"
  os.mkdir(originalSeedDir)
  seedDir = activeDir + "/seeds"
  os.mkdir(seedDir)
  taskDir = activeDir + "/tasks"
  os.mkdir(taskDir)

  #Copy the provided seed corpus
  for seed in os.listdir(seed_corpus):
    if os.path.isfile(os.path.join(seed_corpus, seed)):
      copyfile(os.path.join(seed_corpus, seed), os.path.join(originalSeedDir, seed))

  #Set common fuzzing options/arguments and subject-specific ones
  common_fuzzing_options = "-m 1G -t 20000+ -x " + dict_file + " -o " + activeDir
  specific_fuzzing_options = common_fuzzing_options + " -i " + originalSeedDir + " -S monitor -T AFLTeam-Monitor "
  put_command = afl_binary + pre_args + " @@" + post_args

  '''
  Some programs might need extra fuzzer-specific argument(s), update put_command accordingly
  
  if binary_name == "binary name":
    put_command = put_command + "other options"
  '''

  #Append common and specific options together to form a full fuzzing command
  #for the fuzzing monitor
  fuzz_command = "afl-fuzz " + specific_fuzzing_options + put_command
  logging.debug("Monitor command: %s", fuzz_command)
  pmonitor = subprocess.Popen(fuzz_command.split(" "))
  logging.debug("Monitor PID: %d", pmonitor.pid)

  #Start other fuzzing instances
  #The fuzzing instances run normal afl-fuzz in the exploration phase 
  #and they run horse-fuzz in the exploitation phase

  exploitMode = False
  curRound = 1
  while True:
    logging.debug("Round_%d, Exploitation: %s", curRound, exploitMode)

    #Step-0 (optional). Save results from the previous round & clean results
    if curRound > 1:
      backupDir = out_folder + "/backup_round_" + str(curRound - 1)
      os.mkdir(backupDir)

      #Save callgraph for analysis/debugging
      if os.path.exists(os.path.join(activeDir, "callgraph.dot")):
        shutil.move(os.path.join(activeDir, "callgraph.dot"), backupDir)

      #Save the defined tasks for analysis/debugging
      if os.path.exists(os.path.join(activeDir, "tasks")):
        shutil.move(os.path.join(activeDir, "tasks"), backupDir)

      #Save intermediate seed corpus
      if os.path.exists(os.path.join(activeDir, "seeds")):
        shutil.move(os.path.join(activeDir, "seeds"), backupDir)

      #Save fuzzing instance-specific artifacts
      for index in range(1, cores):
        fuzzerDir = os.path.join(activeDir, "fuzzer_" + str(index + (cores - 1) * (curRound - 2)))
        logging.debug("Saving: %s", fuzzerDir)
        fuzzerLog = fuzzerDir + ".log"
        #save fuzzer's artifacts
        if os.path.exists(fuzzerDir):
          shutil.move(fuzzerDir, backupDir)
          logging.debug("Saving to: %s", backupDir)
        #save fuzzer log
        if os.path.exists(fuzzerLog):
          shutil.move(fuzzerLog, backupDir)

    #Step-1. Prepare seed corpus
    seed_corpus = os.path.join(activeDir, "monitor/queue")
    if curRound == 1:
      seed_corpus = originalSeedDir

    #Create a new seed dir if needed
    if not os.path.exists(seedDir):
      os.mkdir(seedDir)
    index = 1
    for seed in os.listdir(seed_corpus):
      if os.path.isfile(os.path.join(seed_corpus, seed)):
        if curRound > 1:
          if ("+cov" not in seed) and ("orig" not in seed):
            continue
        copyfile(os.path.join(seed_corpus, seed), os.path.join(seedDir, "seed_" + str(index)))
        index = index + 1
    
    logging.debug("Is CG acyclic?: %s", nx.is_directed_acyclic_graph(CG))

    #Step-2. Do task generation in exploitation mode
    if exploitMode:
      #Update callgraph first     
      logging.debug("Nodes-before-update: %d", len(CG.nodes))
      logging.debug("Edges-before-update: %d", len(CG.edges))
      covered_funcs = nxp.update_callgraph(binary_name, pre_args, post_args, CG, v_fname_dict, fname_v_dict, profiling_binary, gcov_binary, gcov_folder, activeDir + "/monitor/queue")
      logging.debug("Nodes-after-update: %d", len(CG.nodes))
      logging.debug("Edges-after-update: %d", len(CG.edges))
    
      logging.debug("Is CG still acyclic?: %s", nx.is_directed_acyclic_graph(CG))

      #prune callgraph and add bbcount
      nxp.prune_callgraph(CG, main_v, v_fname_dict, fname_v_dict, fname_bbs_dict)

      #Create a directory to store all tasks if necessary
      if not os.path.exists(taskDir):
        os.mkdir(taskDir)

      #Then do graph partitioning -- all partitioning algorithms are implemented in the tasks module
      #Tasks will be saved into the newly created taskDir
      if algorithm == "dac":
        #the list of nodes is not shuffled before partitioning
        dac.partition(CG, v_fname_dict, main_v, fname_src_dict, cores - 1, taskDir, False)

      if algorithm == "lukes":
        lukes.partition(CG, main_v, v_fname_dict, fname_src_dict, fname_bbs_dict, covered_funcs, cores - 1, taskDir)

    #Write updated call graph to a file for analysis/debugging
    nx.drawing.nx_pydot.write_dot(CG, os.path.join(activeDir, "callgraph.dot"))

    #Step-3. Start fuzzing instances
    popens = []
    for index in range(1, cores):
      #Set up fuzzing command
      if exploitMode:
        specific_fuzzing_options = common_fuzzing_options + " -i " + seedDir + " -S fuzzer_" + str(index + (cores - 1) * (curRound - 1)) + " -p " + taskDir + "/task_" + str(index) + ".txt "
        put_command = horsefuzz_binary + pre_args + " @@" + post_args

        '''
        Some programs might need extra fuzzer-specific argument(s), update put_command accordingly
        
        if binary_name == "binary name":
          put_command = put_command + "other options"
        '''

        fuzz_command = "horse-fuzz " + specific_fuzzing_options + put_command
      else:
        specific_fuzzing_options = common_fuzzing_options + " -i " + seedDir + " -S fuzzer_" + str(index) + " "
        put_command = afl_binary + pre_args + " @@" + post_args

        '''
        Some programs might need extra fuzzer-specific argument(s), update put_command accordingly
        
        if binary_name == "binary name":
          put_command = put_command + "other options"
        '''

        fuzz_command = "afl-fuzz " + specific_fuzzing_options + put_command
      
      logging.debug("Fuzzer command: %s", fuzz_command)

      #Start fuzzing
      logfile = open(activeDir + '/fuzzer_' + str(index + (cores - 1) * (curRound - 1)) + '.log','w')
      p = subprocess.Popen(fuzz_command.split(" "), stdout=logfile)
      logging.debug("PID: %d", p.pid)
      popens.append(p)
      time.sleep(5)

    #Step-4. wait until the stopping criteria meet
    if exploitMode:
      stopping.should_stop_timeout(expl_timeout)
    else:
      stopping.should_stop_timeout(scanning_timeout)

    #Send SIGTERM signal to stop fuzzing instances
    for p in popens:
      os.kill(p.pid, signal.SIGTERM)
      p.wait()
    
    #Step-5. Finalize current round and switch mode if needed
    if not exploitMode:
      exploitMode = not exploitMode

    curRound = curRound + 1
    #Assumption: (total_timeout - scanning_timeout) % expl_timeout = 0
    if curRound == (total_timeout - scanning_timeout) / expl_timeout + 2:
      break

  os.kill(pmonitor.pid, signal.SIGTERM)
  pmonitor.wait()

  logging.debug("AFLTeam ends!!!")

  return 0
# Parse the input arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-bn','--binary',type=str,required=True,help="Binary name (e.g., pngimage)")
    parser.add_argument('-ab','--afl_binary',type=str,required=True,help="Full path to the afl-instrumented binary")
    parser.add_argument('-hb','--horsefuzz_binary',type=str,required=True,help="Full path to the fuzzing binary")
    parser.add_argument('-pb','--profiling_binary',type=str,required=True,help="Full path to the profiling binary")
    parser.add_argument('-gb','--gcov_binary',type=str,required=True,help="Full path to the gcov binary")
    parser.add_argument('-gf','--gcov_folder',type=str,required=True,help="Full path to the gcov folder")
    parser.add_argument('-ea1','--pre_arguments',type=str,required=True,help="Extra argument(s) to run the binary that needs to be in front of @@")
    parser.add_argument('-ea2','--post_arguments',type=str,required=True,help="Extra argument(s) to run the binary that needs to be behind @@")
    parser.add_argument('-i','--seed_corpus',type=str,required=True,help="Full path to the seed corpus")
    parser.add_argument('-o','--out_folder',type=str,required=True,help="Full path to the output folder keeping all results")
    parser.add_argument('-x','--dict',type=str,required=True,help="Full path to the dictionary file")
    parser.add_argument('-d','--dot_file',type=str,required=True,help="Full path to dot file generated by LLVM opt")
    parser.add_argument('-f','--func_ids',type=str,required=True,help="Full path to func_ids.log generated by HorseFuzz afl-clang-fast")
    parser.add_argument('-b','--func_bbs',type=str,required=True,help="Full path to func_bbs.log generated by HorseFuzz afl-clang-fast")
    parser.add_argument('-c','--cores',type=int,required=True,help="Number of CPU cores")
    parser.add_argument('-a','--algorithm',type=str,required=True,help="Partitioning algorithm (e.g., lukes, dac)")
    parser.add_argument('-tt','--total_timeout',type=int,required=True,help="Timeout in seconds for the whole experiment")
    parser.add_argument('-st','--scanning_timeout',type=int,required=True,help="Timeout in seconds for scanning/exploration phase")
    parser.add_argument('-et','--expl_timeout',type=int,required=True,help="Timeout in seconds for exploitation phase")
    args = parser.parse_args()
    main(args.binary, args.afl_binary, args.horsefuzz_binary, args.profiling_binary, args.gcov_binary, args.gcov_folder, args.pre_arguments, args.post_arguments, args.seed_corpus, args.out_folder, args.dict, args.dot_file, args.func_ids, args.func_bbs, args.cores, args.algorithm, args.total_timeout, args.scanning_timeout, args.expl_timeout)
