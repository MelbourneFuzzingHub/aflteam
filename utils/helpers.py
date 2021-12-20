#check if a tuple of (srcName, hashId) exist
def tuple_exist(tDict, tKey, srcName, hashId):
  for (tName, tHash) in tDict[tKey]:
    if ((tName == srcName) and (tHash == hashId)):
      return True
  return False
