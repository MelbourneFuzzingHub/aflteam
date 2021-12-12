import time

#Simple stopping condition based on timeout
def should_stop_timeout(timeout):
  time.sleep(timeout)
  return 0
