from config import *
# Get supermajority
fileHandle = open(debug_log, "r")
lineList = fileHandle.readlines()
fileHandle.close()
supermajority_pos_num = 0
supermajority_percentage = 0
for x in range(60):
    line = lineList[-x]
    if "Version 5 block" in line:
        print(line)
