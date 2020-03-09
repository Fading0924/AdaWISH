import os
import sys
import re
import math
import argparse

parser = argparse.ArgumentParser("Log analyzer configure")
parser.add_argument('-d', '--logdir', type=str, default="../data/isingModel", help="dirs for raw LOG files output by CPLEX")
parser.add_argument('-n', '--name', type=str, default="ising", help="PBS job name")
args = parser.parse_args()
hasAce = False
hasDAI = True
datadir = args.logdir
name = args.name
outputdir = "../log/" + name
repeatTime = 1

c = 5
delta = 0.01
def getSamplenb(nbvar):
    intermediate = math.sqrt(pow(2,c))
    k = intermediate - 1 / intermediate
    prob = 1 - 1 / pow(k, 2)
    alpha = math.log(2) * ((prob - 0.5) ** 2) / (2 * prob)
    T = int(math.ceil(math.log(nbvar)*math.log(1.0/delta)/alpha))
    return T

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

def LogProcess(folderName, depth, T):
    w=[]
    Samples=[] 
    if depth == 0:
        samplenb = 1
    else:
        samplenb = T
    samplenb = 10
    for t in range(1, samplenb+1):
        fileName = "%s.xor%d.loglen%d.%d.ILOGLUE.uai.LOG" % (folderName , depth , 0 , t)					# sample number
        if not os.path.exists("../output/{}/{}".format(folderName, fileName)):
            continue
        with open("../output/{}/{}".format(folderName, fileName), 'r') as f:
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


def walkThrough():
    if not os.path.exists(outputdir):
        os.mkdir(outputdir)
    var = re.compile(r"var[0-9]+")
    num = re.compile(r"[0-9]+")
    fac = re.compile(r"[0-9]+\.[0-9]+")
    inf = re.compile(r"-Infinity")
    for file in sorted(os.listdir(datadir)):
        if os.path.splitext(file)[1] != ".uai":
            continue
        varstr = var.search(file).group(0)
        nbvar = int(num.search(varstr).group(0))
        print("Processing output of file: {}".format(file))
        T = getSamplenb(nbvar)
        print("    dealing with {:d} samples per depth".format(T))
        for i in range(repeatTime):

            # dealing with log files in folders
            # folderName = "{}_{:d}".format(os.path.splitext(file)[0], i)
            # outfile = "{}/{}_{:d}".format(outputdir, os.path.splitext(file)[0], i)
            folderName = "{}".format(os.path.splitext(file)[0])
            outfile = "{}/{}".format(outputdir, os.path.splitext(file)[0])
            if not os.path.exists("../output/"+folderName):
                print("    cannot find folder {}, skip".format(folderName))
            else:
                print("    processing folder {}".format(folderName))
                with open(outfile, 'w') as f:
                    f.write(str(nbvar)+'\n')
                    for d in range(nbvar+1):
                        f.write(str(LogProcess(folderName, d, T))+'\n')

            # dealing with ace output
            if hasAce:
                fileName = os.path.splitext(file)[0]
                outfile = "{}/{}_ace".format(outputdir, os.path.splitext(file)[0])
                if not os.path.exists("../output/"+fileName):
                    print("    cannot find ace output {}, skip".format(fileName))
                else:
                    
                    with open("../output/"+fileName, 'r') as rf, open(outfile, 'w') as wf:
                        if not os.path.exists("../output/"+fileName):
                            wf.write("0")
                        else:
                            line = rf.readlines()[0]
                            res = fac.search(line)
                            if res != None:
                                wf.write(fac.search(line).group(0))
                            elif inf.search(line) != None:
                                wf.write(inf.search(line).group(0))
                            else:
                                print("Unknown data type in " + fileName)
                            

            # dealing with libDAI output
            if hasDAI:
                for alg in ['bp', 'jt', 'mf', 'trwbp']:
                    fileName = file + "_{}_PR".format(alg)
                    outfile = "{}/{}_{}_PR".format(outputdir, os.path.splitext(file)[0], alg)
                    if not os.path.exists("../output/"+fileName):
                        print("    cannot find libDAI output {}, skip".format(fileName))
                    else:
                        with open("../output/"+fileName, 'r') as rf, open(outfile, 'w') as wf:
                            ans = fac.search(rf.readlines()[2]).group(0)
                            wf.write(ans)
                            


if __name__ == "__main__":
    walkThrough()
