#common data types
class Function:
  def __init__(self, name, fname, fpath, btotal, bcovered):
    self.name = name
    self.fname = fname
    self.fpath = fpath
    self.btotal = btotal
    self.bcovered = bcovered

#global variables
VERBOSE_LEVEL = 3 #set this to a higher value to see more verbose info in aflteam.log
                  #current max level is 3

#FIXME: we should not hardcode the colors list
#this list is used to set colors for different tasks/partitions on the call graph
colors = ["red", "green", "blue", "orange", "purple", "black"]
COLOR_COUNT = len(colors)

spare_functions_set = set() #set of all functions that are not attached to the current callgraph 
profiled_seeds = [] #list of all seed inputs that have been used
                    #for profiling
