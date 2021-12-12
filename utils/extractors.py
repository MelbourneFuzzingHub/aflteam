from utils import helpers

#process func_ids.log file produced by horsefuzz-clang-fast
def extract_fname_src_dict(func_ids):
  fname_src_dict = dict()

  f = open(func_ids, "r")
  for line in f:
    #sample line: png.c:png_set_sig_bytes 4276553628
    tmpStrs = line.strip().split(":")
    if len(tmpStrs) != 2:
      continue
    srcName = tmpStrs[0]
    funcName = tmpStrs[1].split(" ")[0]
    hashId = tmpStrs[1].split(" ")[1]
    
    if funcName in fname_src_dict.keys():
      if helpers.tuple_exist(fname_src_dict, funcName, srcName, hashId) == False:
        fname_src_dict[funcName].append((srcName, hashId))
    else:
      fname_src_dict[funcName] = [(srcName, hashId)]
  f.close()
  return fname_src_dict

#process func_bbs.log file produced by horsefuzz-clang-fast
def extract_fname_bbs_dict(func_bbs):
  fname_bbs_dict = dict()

  f = open(func_bbs, "r")
  for line in f:
    #sample line: png.c:png_get_header_version: 1
    tmpStrs = line.strip().split(":")
    if len(tmpStrs) != 3:
      continue
    srcName = tmpStrs[0].strip()
    funcName = tmpStrs[1].strip()
    bbCount = int(tmpStrs[2].strip())
   
    #ignore functions with no instrumented basic blocks 
    if bbCount > 0:
      if funcName in fname_bbs_dict.keys():
        if helpers.tuple_exist(fname_bbs_dict, funcName, srcName, bbCount) == False:
          fname_bbs_dict[funcName].append((srcName, bbCount))
      else:
        fname_bbs_dict[funcName] = [(srcName, bbCount)]

  f.close()
  return fname_bbs_dict
