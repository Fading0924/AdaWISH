#----------------------------------------------------------------------------------------
# Copyright, 2013:
#
# Stefano Ermon 		- Cornell University 			, ermonste@cs.cornell.edu
# Ashish Sabharwal 		- IBM Watson Research Center 	, ashish.sabharwal@us.ibm.com
#----------------------------------------------------------------------------------------

import sys
import math
import random
import os
import argparse
import time
import re
import numpy as np

import matplotlib
matplotlib.use('Agg') # Must be before importing matplotlib.pyplot or pylab!
import pylab

# version number
__version__ = '1.0'

#########################################
# Usage Information:
# run "python WISH.py -h" for help
#########################################

parser = argparse.ArgumentParser(description='Estimate the partition function using the WISH algorithm and CPLEX for the optimization.')

parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
parser.add_argument("infile", help="Graphical model (in UAI format)")
parser.add_argument("outfolder", help="Folder where logs are stored")
parser.add_argument('-alpha', '--alpha', type=float, help="Accuracy alpha", default=0.0042)
parser.add_argument('-delta', '--delta', type=float, help="Failure probability delta", default=0.01)
parser.add_argument('-timeout', '--timeout', type=int, help="Timeout for each optimization instance (seconds)", default=1000)
parser.add_argument('-parallel', type=bool, default=False, help="use parallel optimization")


args = parser.parse_args()


print("Reading factor graph from " + args.infile)


queryCnt = 0

fileName, fileExtension = os.path.splitext(args.infile)
limit = 4500
c = 2
rate = (2 ** c) - 1
ind = 0
origNbrFactor = 0
origNbrVar = 0
with open(args.infile, "r") as inputfile:
    for l in inputfile:
        if not l.strip()=='':
            ind = ind +1
            if ind==2:
                origNbrVar=int(l)
            elif ind==3:
                l = l.rstrip("\n")
            elif ind==4:			## add xor cpt tabe
                origNbrFactor = int(l)
            elif ind>5:
                break
print("Model with " + str(origNbrVar) + "variables and "+str(origNbrFactor) +" factors")

depth = origNbrVar

T = int(math.ceil(math.log(origNbrVar)*math.log(1.0/args.delta)/args.alpha))

print("Using " + str(T) +" samples per level")




# Generate PBS job submitting command string,
# related to the variables' name set in job launch script and file path
# determined before executioin
queue = "yexiang"
# variables
basedir = "/home/wang4588/adawish/src"
tmpdir = "/tmp/"
outdir = args.outfolder
infile = args.infile
timeout = "1000s"
vstring = "-v basedir={},tmpdir={},outdir={},file={},timeout={}".format(
                    basedir, tmpdir, outdir, infile, timeout)
# node occupation policies
# resources
nodes = "1"
ppn = "1"
walltime = "00:10:00"
rstring = "-l walltime={},nodes={}:ppn={},naccesspolicy=singleuser".format(
                    walltime, nodes, ppn)
# launch script
script = "LaunchIloglue.sh"

command_string = "qsub -q {} {} {}".format(queue, rstring, vstring)
os.system("mkdir "+basedir+"/../log/"+args.outfolder)
def median(alist):
    
    if len(alist)==1:
        return alist[0]
    else:
        srtd = sorted(alist) # returns a sorted copy
        mid = int(len(alist)/2)   # remember that integer division truncates

        # print("Debug: The type of mid is ".format(type(mid)))
        if len(alist) % 2 == 0:  # take the avg of middle two
            return (srtd[mid-1] + srtd[mid]) / 2.0
        else:
            return srtd[mid]
            
def LogProcess(depth):
    w=[]
    Samples=[] 
    if depth == 0:
        samplenb = 1
    else:
        samplenb = 10
    for t in range(1, samplenb+1):
        outfilenamelog = "%s.xor%d.loglen%d.%d.ILOGLUE.uai.LOG" % (os.path.basename(args.infile) , depth , 0 , t)					# sample number
        with open(basedir+"/../log/"+args.outfolder +"/"+ outfilenamelog, 'r') as f:
            #check if solved to optimality
            lines = f.read()
            #entries = re.search("Optimum: (\d+) log10like: ([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?) prob: ([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?) in (\d+) backtracks and (\d+) nodes and ([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?) seconds", lines)
            entriesoo = re.search("Solution status = Optimal", lines)
            entries = re.search("Solution value log10lik = ([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)", lines)
            if entries is not None and entriesoo is not None:
                # print(entries.group(1))
                # print(entries.group(2))
                w.append([float(entries.group(1)),True])
                entriesSol = re.search("Optimal solution: (\d+)", lines)
                if entriesSol is not None:
                    Samples.append([float(entries.group(1)),True,entriesSol.group(1)])
            else:
                entries2 = re.findall("\n(\s+)(\d+)(\s+)(\d+)(\s+)([-+]?\d+\.\d+)(\s+)(\d+)(\s+)(\s+|[-+]?\d+\.\d+)(\s+)([-+]?\d+\.\d+)", lines)
                if entries2:
                    # find last entry
                    #print entries2
                    if is_number(entries2[-1][-3]):
                        #print "found something " + str(float(entries2[-1][-3]))
                        w.append([float(entries2[-1][-3]),False])
                    else:
                        w.append([float("-inf"),True])			# problem is unsat
                    entriesSol = re.findall("Current solution: (\d+)", lines)
                    if entriesSol:
                        #print entriesSol[-1]
                        Samples.append([float(entries2[-1][1]),False,entriesSol[-1]])
                else:
                    # Inconsistency detected!
                    entries3 = re.search("No solution in (\d+) backtracks and", lines)
                    entries4 = re.search("Inconsistency detected!", lines)
                    entries5 =	re.search("Infeasibility row", lines)
                    entries6 =	re.search("Failed to optimize LP", lines)							
                    entries7 =	re.search("Infeasible column", lines)
                    
                    if (entries3 is not None or entries4 is not None or entries5 is not None or entries6 is not None or entries7 is not None):
                        #nothing = 34
                        w.append([float("-inf"),True])			# problem is unsat
                    else:
                        print("ERROR reading logs", outfilenamelog)
            #New solution: 0 log10like: 0 prob: 1 (0 backtracks, 24 nodes, depth 25)
            #Optimum: 91499957 log10like: -3.97379 prob: 0.00010622 in 299 backtracks and 600 nodes and 0.08 seconds.

    results = [t[0] for t in w]
    if len(results) > 0:
        return median(results)
    else:
        return float("-inf")

def XorQuery(wb, queried, d):
    global queryCnt
    print("Query " + str(d))
    if queried[d] == 1:
        return wb[d]
    queryCnt += 1
    if d == 0:
        samplenb = 1
    else:
        samplenb = T
    for t in range(1, samplenb+1):
        if not args.parallel:
            outfilenamelog = "%s.xor%d.loglen%d.%d.ILOGLUE.uai.LOG" % (os.path.basename(args.infile) , d , 0 , t)
            cmdline = ("timeout %d ../bin/AdaWish -paritylevel 1 -number %d -seed 10 %s > %s") % (args.timeout , d , args.infile , basedir+"/../log/"+args.outfolder +"/"+ outfilenamelog)
            os.system(cmdline)
        else:
            while True:
                current_queue_length = os.popen("qstat -u wang4588 | wc -l")
                curlen = int(re.split(r"\n", current_queue_length.read())[0])
                if curlen > 3000:
                    time.sleep(5)
                else:
                    break
            # current_queue_length = os.popen("qstat -u wang4588 | wc -l")
            # while re.search(str(limit), current_queue_length.read()) is not None:
            #     time.sleep(5)
            arg_string = ",level={},len={},sample={} {}".format(str(d), str(0), str(t), script)
            os.system(command_string+arg_string)


    while True:
        finished = True
        for t in range(1, samplenb+1):
            outfilenamelog = "%s.xor%d.loglen%d.%d.ILOGLUE.uai.LOG" % (os.path.basename(args.infile) , d , 0 , t)
            if not args.parallel:
                finished = finished and os.path.exists(args.outfolder+"/"+outfilenamelog)
            else:
                # print(basedir+"/../log/"+args.outfolder+"/"+outfilenamelog)
                finished = finished and os.path.exists(basedir+"/../log/"+args.outfolder+"/"+outfilenamelog)
                # print(finished)
        if finished:
            break;
        time.sleep(5)

    wb[d] = LogProcess(d)
    queried[d] = 1

def XorSearch(wb, interval, queried, l, r):
    wl = XorQuery(wb, queried, max(l - c, 0))
    wr = XorQuery(wb, queried, min(r + c, depth))
    if l + 1 == r or wl <= wr * rate:
        # stop condition
        val = (wl + wr) / 2
        for i in range(l + 1, r):
            wb[i] = val
            interval[i - 1] = val
    else:
        mid = int((l + r) / 2)
        XorQuery(wb, queried, mid)
        XorSearch(wb, interval, queried, l, mid)
        XorSearch(wb, interval, queried, mid, r)

def XorAdaWish():
    global queryCnt
    queryCnt = 0
    queried = np.zeros(depth + 1)
    wb = np.zeros(depth + 1)
    interval = np.zeros(depth)
    XorQuery(wb, queried, 0)
    XorQuery(wb, queried, depth)
    XorSearch(wb, interval, queried, 0, depth)

    curmax = wb[0]
    W = np.power(10, wb - curmax).sum()
    W += ((np.power(2, range(depth)) - 1) * np.power(10, interval - curmax)).sum()
    W = np.log10(W) + curmax


    print("log10 partition function W = " + str(W))
    print("query time = " + str(queryCnt))

if __name__ == "__main__":
    XorAdaWish()