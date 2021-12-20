import os
import subprocess
import sys
import networkx as nx
import logging
from datetime import datetime
import math
from enum import Enum

from utils import helpers
import globals

class ParsingState(Enum):
  INITIAL = 1
  PARSING_FUNCTION_INFO = 2
  PARSING_FILE_INFO = 3

#extract callgraph given a .dot file
def extract_callgraph(dot_file):
  logging.debug("extract_callgraph starts at: %s", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
  #Get the initial callgraph
  #import the call graph from the .dot file
  CG = nx.DiGraph(nx.drawing.nx_pydot.read_dot (dot_file))

  #creat a dictionary mapping from node/vertex id to function name
  #and a dictionary mapping from function name to node/vertex id
  v_fname_dict = dict()
  fname_v_dict = dict()
  deleted_nodes = []
  for n in CG.nodes:
    try:
      v_fname_dict[n] = CG.nodes[n]['label'].replace('{','').replace('}','').replace('"','')
      fname_v_dict[CG.nodes[n]['label'].replace('{','').replace('}','').replace('"','')] = n
    except KeyError:
      #normally it happens when a node has no label
      deleted_nodes.append(n)
      pass

  #delete all nodes having no label
  for v in deleted_nodes:
    CG.remove_node(v)

  #find the main node/vertex
  main_v = None
  for n in CG.nodes:
    try:
      if "{main}" in CG.nodes[n]['label']:
        main_v = n
    except KeyError:
      pass
  if main_v == None:
    print("Error! No function main is found in the call graph.")
    exit()

  logging.debug("extract_callgraph ends at: %s", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
  return (CG, v_fname_dict, fname_v_dict, main_v)

#remove a node from a given graph and associated dictionaries
def remove_node(CG, v, v_fname_dict, fname_v_dict):
  fname_v_dict.pop(v_fname_dict[v], None)
  v_fname_dict.pop(v, None)
  CG.remove_node(v)

#prune callgraph
def prune_callgraph(CG, main_v, v_fname_dict, fname_v_dict, fname_bbs_dict):
  logging.debug("prune_callgraph starts at: %s", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

  logging.debug("Nodes-before-prunning-1: %d", len(CG.nodes))
  logging.debug("Edges-before-prunning-1: %d", len(CG.edges))
  #delete nodes that have no bb count information
  deleted_nodes = []
  try:
    for v in CG.nodes:
      if v_fname_dict[v] not in fname_bbs_dict:
        deleted_nodes.append(v)
      else:
        for (srcFileName, bbCount) in fname_bbs_dict[v_fname_dict[v]]:
          CG.nodes[v]['label'] = (str(CG.nodes[v]['label'])).replace("\"","").replace("{","").replace("}","") + "\\\\n" + str(bbCount)
          break
  except KeyError:
    pass

  for v in deleted_nodes:
    try:
      if globals.VERBOSE_LEVEL > 3:
        logging.debug("Deleted-phase-1: %s", v_fname_dict[v])
      globals.spare_functions_set.remove(v_fname_dict[v])
    except KeyError:
      pass
    remove_node(CG, v, v_fname_dict, fname_v_dict)

  logging.debug("Nodes-before-prunning-2: %d", len(CG.nodes))
  logging.debug("Edges-before-prunning-2: %d", len(CG.edges))
  #And delete disconnected nodes
  deleted_nodes = []
  try:
    for v in CG.nodes:
      if CG.in_degree(v) == 0 and CG.out_degree(v) == 0:
        deleted_nodes.append(v)
  except KeyError:
    pass

  for v in deleted_nodes:
    if globals.VERBOSE_LEVEL > 3:
      logging.debug("Deleted-phase-2: %s", v_fname_dict[v])
    globals.spare_functions_set.add(v_fname_dict[v])
    remove_node(CG, v, v_fname_dict, fname_v_dict)

  logging.debug("Nodes-before-prunning-3: %d", len(CG.nodes))
  logging.debug("Edges-before-prunning-3: %d", len(CG.edges))
  #And delete all nodes that are not reachable from main
  deleted_nodes = []
  try:
    for v in CG.nodes:
      if v == main_v:
        continue

      #logging.debug("Checking reachability of " + v_fname_dict[v])
      try:
        tempLen = nx.shortest_path_length(CG, main_v, v)  
      except nx.NetworkXNoPath:
        deleted_nodes.append(v)
  except KeyError:
    logging.debug("We should not be here")
    pass

  for v in deleted_nodes:
    if globals.VERBOSE_LEVEL > 3:
      logging.debug("Deleted-phase-3: %s", v_fname_dict[v])
    globals.spare_functions_set.add(v_fname_dict[v])
    remove_node(CG, v, v_fname_dict, fname_v_dict)

  logging.debug("Nodes-after-all-prunning: %d", len(CG.nodes))
  logging.debug("Edges-after-all-prunning: %d", len(CG.edges))
  logging.debug("prune_callgraph ends at: %s", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

#check and insert functions from tmpFunctions list to Functions list
def update_function_list(Functions, tmpFunctions):
  for f1 in tmpFunctions:
    '''
    Handle cases in which we have more than one function having the same name.
    For example, two test drivers can both have their main function.
    To distinguish them, normally we need to use the source file as well.
    However, in this implementation, we assume that the bcovered info of the target function 
    has the largest value.
    '''
    isExisting = False
    for f2 in Functions:
      if f1.name == f2.name:
        if f1.bcovered > f2.bcovered:
          f2.fname = f1.fname
          f2.fpath = f1.fpath
          f2.btotal = f1.btotal
          f2.bcovered = f1.bcovered     
        #break as long as f1.name equals f2.name
        #so that we do not insert the same function name from files that are not targeted
        isExisting = True
        break

    if isExisting == False:
      Functions.append(f1)

#add nodes & edges based on profiling result 
def add_nodes_and_edges(CG, v_fname_dict, fname_v_dict, logFilePath):
  covered_funcs = []
  f = open(logFilePath, "r")
  edgeSet = set([])

  for line in f:
    # sample line: Function: pngmem.c:png_malloc_base->malloc
    tmpStrs = line.strip().split(" ")[1].strip().split("->")
    if len(tmpStrs) == 2:
      if line.strip() not in edgeSet:
        edgeSet.add(line.strip())
        caller = tmpStrs[0].strip().split(":")[1]
        callee = tmpStrs[1].strip()

        if caller not in covered_funcs:
          covered_funcs.append(caller)
        if callee not in covered_funcs:
          covered_funcs.append(callee)

        caller_v = None
        callee_v = None
        if caller not in fname_v_dict:
          #add a new node/vertice
          CG.add_node(caller, style = "dashed",)
          fname_v_dict[caller] = caller
          try:
            globals.spare_functions_set.remove(caller)
          except KeyError:
            pass
          
        if callee not in fname_v_dict:
          #add a new node/vertice
          CG.add_node(callee, style = "dashed",)
          fname_v_dict[callee] = callee
          try:
            globals.spare_functions_set.remove(callee)
          except KeyError:
            pass

        caller_v = fname_v_dict[caller]
        callee_v = fname_v_dict[callee]

        v_fname_dict[caller_v] = caller
        v_fname_dict[callee_v] = callee
        try:
          CG.nodes[caller_v]['label'] = "{" + caller + "}"
          CG.nodes[caller_v]['shape'] = "record"
          #CG.nodes[caller_v]['color'] = "red"
          #CG.nodes[caller_v]['fontcolor'] = "red"
          CG.nodes[callee_v]['label'] = "{" + callee + "}"
          CG.nodes[callee_v]['shape'] = "record"
          #CG.nodes[callee_v]['color'] = "red"
          #CG.nodes[callee_v]['fontcolor'] = "red"
        except KeyError:
          logging.debug("KeyError: " + caller + ": " + callee + ": " + str(caller_v) + ": " + str(callee_v))
          sys.exit()

        if CG.has_edge(caller_v, callee_v) == False:
          CG.add_edge(caller_v, callee_v, style = "dashed")
  return covered_funcs

def extract_gcov_profiling(gcov_folder):
  Functions = []
  #update covered branches based on gcov results
  with open(os.devnull, 'w') as FNULL:
    #run gcov on the folder keeping gcov-enabled binary
    command = "run-gcov.sh " + gcov_folder
    p = subprocess.Popen(command.split(" "), stdout=FNULL, stderr=FNULL)
    p.wait()

    #process gcov.log file
    flog = open(gcov_folder + "/gcov.log", "r")

    curParsingState = ParsingState.INITIAL
    curFunction = globals.Function("", "", "", 0, 0)

    tmpFunctions = []
    for line in flog:
      #Only process lines of interest and ignore others
      if line.startswith("Function"):
        #Example: Function 'png_write_image'
        tmpStrs = line.split("'")
        curFunction.name = tmpStrs[1]
        #Update parsing state
        curParsingState = ParsingState.PARSING_FUNCTION_INFO
        continue
      if line.startswith("File "):
        #Example: File 'pngimage.c'
        tmpStrs = line.split("'")
        fpath = tmpStrs[1]
        tmpStrs = fpath.split("/")
        fname = tmpStrs[len(tmpStrs) - 1]
        #Update all functions in a specific source file
        for f in tmpFunctions:
          f.fname = fname
          f.fpath = fpath
        #Update parsing state
        curParsingState = ParsingState.PARSING_FILE_INFO
        continue

      if line.startswith("Taken at least once"):
        if curParsingState == ParsingState.PARSING_FUNCTION_INFO:
          #Example: Taken at least once:52.94% of 34
          tmpStrs = line.split("% of ")
          btotal = int(tmpStrs[1].split("\n")[0])
          bper = float(tmpStrs[0].split(":")[1])
          bcovered = math.floor((bper * btotal) / 100)
          curFunction.btotal = btotal
          curFunction.bcovered = bcovered
          continue
     
      #check for end of function/file
      if line.startswith("\n"):
        if curParsingState == ParsingState.PARSING_FUNCTION_INFO:
          #Add the curFunction to the tmpFunctions list
          tmpFunctions.append(curFunction)
        if curParsingState == ParsingState.PARSING_FILE_INFO:
          #Move functions from tmpFunctions list to Functions list
          update_function_list(Functions, tmpFunctions)
          #Clear tmpFunctions
          tmpFunctions.clear()
        #Initialize a new function
        curFunction = globals.Function("", "", "", 0, 0)
        #Update parsing state
        curParsingState = ParsingState.INITIAL
  return Functions

#update callgraph based on function call profiling information
def update_callgraph(binary_name, pre_args, post_args, CG, v_fname_dict, fname_v_dict, profiling_binary, gcov_binary, gcov_folder, seed_dir, isFirstRun):
  logging.debug("update_callgraph starts at: %s", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
  #keep track all functions that have been dynamically covered
  covered_funcs = []

  #Delete the existing covered_functions.log
  logFilePath = "/tmp/" + binary_name + "/covered_functions.log"
  if os.path.exists(logFilePath):
    os.remove(logFilePath)

  #Run the profiling binary with the seed inputs
  with open(os.devnull, 'w') as FNULL:
    sCount = 0
    for seed in os.listdir(seed_dir):
      if not isFirstRun:
        #only run profiling of coverage-increasing inputs
        if ("+cov" not in seed):
          #logging.debug("Skip not +cov: %s", seed)
          continue
        #skip the profiled ones
        if seed in globals.profiled_seeds:
          #logging.debug("Skip profiled: %s", seed)
          continue

        globals.profiled_seeds.append(seed)

      if globals.VERBOSE_LEVEL > 3:
        logging.debug("isFirstRun: %s, seed to be executed: %s", isFirstRun, seed)

      if os.path.isfile(os.path.join(seed_dir, seed)):
        #run profiling binary
        command = "timeout -k 0 5s " + profiling_binary + pre_args + " " + os.path.join(seed_dir, seed) + post_args

        '''
        Some programs might need extra fuzzer-specific argument(s), update put_command accordingly

        if binary_name == "binary name":
          command = command + "other options"
        '''

        p = subprocess.Popen(command.split(" "), stdout=FNULL, stderr=FNULL)
        p.wait()

        #run gcov binary
        command = "timeout -k 0 5s " + gcov_binary + pre_args + " " + os.path.join(seed_dir, seed) + post_args

        '''
        Some programs might need extra fuzzer-specific argument(s), update put_command accordingly

        if binary_name == "binary name":
          command = command + "other options"
        '''

        p = subprocess.Popen(command.split(" "), stdout=FNULL, stderr=FNULL)
        p.wait()

      sCount = sCount + 1

  covered_funcs = add_nodes_and_edges(CG, v_fname_dict, fname_v_dict, logFilePath)

  Functions = extract_gcov_profiling(gcov_folder)

  #Update vertices' properties (btotal, bcovered_cur, bcovered_prev)
  for f in Functions:
    if f.name in fname_v_dict:
      v = fname_v_dict[f.name]
      v_dict = CG.nodes[v]
      #Check if the btotal property has been set
      if v_dict.get('btotal') is None:
        CG.nodes[v]['btotal'] = f.btotal
        CG.nodes[v]['bcovered_pre'] = 0
        CG.nodes[v]['bcovered_cur'] = f.bcovered
      else:
        CG.nodes[v]['bcovered_pre'] = CG.nodes[v]['bcovered_cur']
        CG.nodes[v]['bcovered_cur'] = f.bcovered

  logging.debug("update_callgraph ends at: %s", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
  return covered_funcs
