import globals

def split(a, n):
  k, m = divmod(len(a), n)
  return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))

#a random partitioning approach
def partition(CG, v_fname_dict, main_v, fname_src_dict, K, out_folder, is_shuffle=True):
  #divide the graph nodes into smaller sets
  divided_sets = []
  
  divided_sets = list(split(range(len(CG.nodes)), K))

  #Output the results
  lnodes = list(CG.nodes)
  reachableFuncSet = set([])
  for kindex in range(K):
    fout = open(out_folder + "/task_" + str(kindex + 1) + ".txt" ,'w')
    for nindex in divided_sets[kindex]:
      try:
        functionName = v_fname_dict[lnodes[nindex]]
        for (srcFileName, hashId) in fname_src_dict[functionName]:
          fout.write(srcFileName + ":" + functionName + '\n')
        reachableFuncSet.add(functionName)

        colorIndex = kindex % (globals.COLOR_COUNT - 1)
        CG.nodes[lnodes[nindex]]['color'] = globals.colors[colorIndex]
        CG.nodes[lnodes[nindex]]['fontcolor'] = globals.colors[colorIndex]
      except KeyError:
        pass

    fout.close()

  return 0
