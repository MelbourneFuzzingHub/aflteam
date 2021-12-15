import os
import networkx as nx
import logging
import math
import networkx.algorithms.community.lukes as lukes
from datetime import datetime
import statistics

from utils import helpers
import globals

#Reference: J. A. Lukes, "Efficient Algorithm for the Partitioning of Trees," in IBM Journal of Research and Development
def partition(CG, main_v, v_fname_dict, fname_src_dict, fname_bbs_dict, covered_funcs, K, out_folder):
  logging.debug("do_partitioning_lukes starts at: %s", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
  #Get minimum arborescence
  logging.debug("Running minimum_spanning_arborescence algorithm ...")
  MSA = nx.minimum_spanning_arborescence(CG)

  total_branches = 0
  for v in MSA.nodes:
    MSA.nodes[v]['label'] = v_fname_dict[v]
    total_branches = total_branches + CG.nodes[v]['btotal']

  #update scores/weights
  scores = []
  for v in MSA.nodes:
    score = (CG.nodes[v]['bcovered_cur'] - CG.nodes[v]['bcovered_pre'] + 1) * (CG.nodes[v]['btotal'] - CG.nodes[v]['bcovered_cur'])
    scores.append(score)

    MSA.nodes[v]['score'] = score #set score with no normalization yet
    if globals.VERBOSE_LEVEL > 2:
      logging.debug("Function %s score: %d, b_pre: %d, b_cur: %d, b_total: %d", v_fname_dict[v], score, CG.nodes[v]['bcovered_pre'], CG.nodes[v]['bcovered_cur'], CG.nodes[v]['btotal'])

  scores.sort()
  median_score = math.floor(statistics.median(scores))
  mean_score = math.floor(statistics.mean(scores))
  logging.debug("Median score: %d, mean score: %d, max score: %d", median_score, mean_score, max(scores))
  if globals.VERBOSE_LEVEL > 2:
    logging.debug(str(("List of scores: ",scores)))

  #normalize the node score on MSA before partitioning using kind-of ReLU-N function
  #where N is a upper threshold
  #TODO: try out other threshold values

  total_score = 0
  for v in MSA.nodes:
    threshold = median_score + mean_score
    if MSA.nodes[v]['score'] > threshold:
      MSA.nodes[v]['score'] = threshold
    total_score = total_score + MSA.nodes[v]['score']

  #write to dot file for debugging
  nx.drawing.nx_pydot.write_dot(MSA, os.path.join(out_folder, "msa-no-colors.dot"))

  #do partitioning using lukes aglrithm
  logging.debug("Running lukes partitioning algorithm ...")
  plist = lukes.lukes_partitioning(MSA, math.ceil(total_score / K), 'score')

  #Divide the list into sublists
  logging.debug("Grouping " + str(len(plist)) + " partitions into " + str(K) + " tasks")
  tasks = helpers.group_tasks(plist, K)
  
  logging.debug("#partitions: %d", len(tasks))
  tIndex = 0
  for task in tasks:
    tIndex = tIndex + 1
    fout = open(out_folder + "/task_" + str(tIndex) + ".txt" ,'w')
    if globals.VERBOSE_LEVEL > 2:
      logging.debug("Partition %d", tIndex)

    outputSet = set()
    #some subtask(s) might not be reachable yet (i.e., no test input can reach functions in a task)
    #if all subtasks are not reachable, bitmap coverage becomes empty and the fuzzing instance stops unexpectedly
    #to handle those cases, we add functions on the shortest path from the main function to a each subtask.
    #And by exploring those functions, the fuzzer may eventually reach subtasks that were unreachable
    for subtask in task:
      pathToMainIncluded = False
      for v in subtask:
        colorIndex = (tIndex-1) % (globals.COLOR_COUNT - 1)
        MSA.nodes[v]['color'] = globals.colors[colorIndex]
        MSA.nodes[v]['fontcolor'] = globals.colors[colorIndex]
        for (src, dst) in MSA.out_edges(v):
          MSA.edges[src, dst]['color'] = globals.colors[colorIndex]

        functionName = v_fname_dict[v]
        if globals.VERBOSE_LEVEL > 2:
          logging.debug("Node: %s", functionName)
        
        try:
          for (srcFileName, hashId) in fname_src_dict[functionName]:
            outputSet.add((srcFileName, functionName))
        except KeyError:
          pass

        if pathToMainIncluded == False:
          #Find the shortest path from main_v to v
          path = nx.shortest_path(CG, main_v, v)
          for v1 in path:
            functionName = v_fname_dict[v1]
            try:
              for (srcFileName, hashId) in fname_src_dict[functionName]:
                outputSet.add((srcFileName, functionName))
            except KeyError:
              pass
          pathToMainIncluded = True

      #output all (srcFileName, functionName) pairs for the current task
      for (srcFileName, functionName) in outputSet:
        fout.write(srcFileName + ":" + functionName + '\n')
      
    fout.close()

  #write to dot file for debugging
  nx.drawing.nx_pydot.write_dot(MSA, os.path.join(out_folder, "msa.dot"))

  logging.debug("do_partitioning_lukes ends at: %s", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
  return
