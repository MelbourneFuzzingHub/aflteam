#check if a tuple of (srcName, hashId) exist
def tuple_exist(tDict, tKey, srcName, hashId):
  for (tName, tHash) in tDict[tKey]:
    if ((tName == srcName) and (tHash == hashId)):
      return True
  return False

'''
Group N small tasks into k bigger tasks (N > k) in such a way that
the number of functions in each big task is more balanced.
This function is implemented based on an algorithm that tries to 
divide an array into k subarrays that have minimum difference
ref: https://stackoverflow.com/questions/59557159/divide-an-array-into-k-partitions-subarray-that-have-minimum-difference
'''
def group_tasks(arr, k):
    result = [[] for _ in range(k)]
    sums = [0] * k
    for x in sorted(arr, key=len, reverse=True):
        i = sums.index(min(sums))
        sums[i] += len(x)
        result[i].append(x)
    return result
