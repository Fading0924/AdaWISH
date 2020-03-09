import os
import sys
import math
import matplotlib
import re
import argparse
import numpy as np
matplotlib.use("Agg")
import matplotlib.pyplot as plt 
colormap = plt.get_cmap('tab10')
matplotlib.rcParams['axes.prop_cycle'] = matplotlib.cycler(color=[colormap(k) for k in [0,1,2,8,6,5,4,3]])
plt.rcParams.update({'font.size': 14})
adaQueryCnt = 0
c=5
def T(origNbrVar):
    intermediate = math.sqrt(pow(2,c))
    k = intermediate - 1 / intermediate
    prob = 1 - 1 / pow(k, 2)
    alpha = math.log(2) * ((prob - 0.5) ** 2) / (2 * prob)
    delta= 0.01
    return int(math.ceil(math.log(origNbrVar)*math.log(1.0/delta)/alpha))
beta = math.log10(1e5)

parser = argparse.ArgumentParser("Generate graphical representation of data")
parser.add_argument('-d', '--dir', type=str, help="path to the folder where you place all the results")
parser.add_argument('-x', '--xAxis', type=int, help="the x axis of the images, whether use varying problem sizes(0) or coupling strength(1) as x axis")
parser.add_argument('-gt', '--groundtruth', type=int, help="the index of the method which provides ground truth")
parser.add_argument('-r', '--repeat', type=int, help="")
parser.add_argument('-e', '--experiment', type=int, help="")
args = parser.parse_args()

def wish(fp):
    with open(fp, 'r') as f:
        lines = f.readlines()
        nbvar = int(lines[0].split()[0])
        weights = []
        for i in range(1, len(lines)):
            weights.append(float(lines[i].split()[0]))
        # for i in range(len(weights), nbvar):
        #     weights.append(weights[-1])
        # print(weights)
        curmax = weights[0]
        if curmax == float("-inf"):
            return 0

        # wind = len(weights) - 2
        # while wind >=0:
        #     if weights[wind] == float("-inf"):
        #         wind -= 1
        #     else:
        #         break
        # for i in range(wind, len(weights) - 1):
        #     weights[i] = weights[wind] * (len(weights) - 2 - i) / (len(weights) - 2 - wind)
        # print(weights)
        W = 1
        nbbar = 1
        for i in range(1, nbvar+1):
            W += pow(10, weights[i] - curmax) * nbbar
            nbbar = nbbar * 2
        
        W = math.log10(W) + curmax
        # print("Queries made by wish = {:d}".format(nbvar+1))
        # print ("Log10 Partition function by wish = {:.12f}".format(W))
        return W

def getValue(mlist, queried, index):
    if queried[index]:
        return mlist[index]
    global adaQueryCnt
    print("query depth = {}, res = {}".format(index, mlist[index]))
    adaQueryCnt += 1
    queried[index] = True
    return mlist[index]

def binarySearch(weights, queried, bcap, wnode, inter, beta, l, r):
    print("Binary Search left={}, right={}".format(l, r))
    def isninf(a):
        return a == float('-inf')
    if r == l + 1:
        # stop condition 1
        bcap[l] = getValue(weights, queried, l)
        bcap[r] = getValue(weights, queried, r)
        if not isninf(bcap[l]) and not isninf(bcap[r]):
            wnode[l] = bcap[l]
            wnode[r] = bcap[r]
            inter[l] = (bcap[l] + bcap[r]) / 2
        else:
            pass
    else:
        upperbound = max(l - c, 0)
        lowerbound = min(r + c, len(wnode) - 1)
        bcap[upperbound] = getValue(weights, queried, upperbound)
        bcap[lowerbound] = getValue(weights, queried, lowerbound)
        if not isninf(bcap[upperbound]) and not isninf(bcap[lowerbound]):
            if bcap[upperbound] >= beta + bcap[lowerbound]:
                mid = int((l + r) / 2)
                binarySearch(weights, queried, bcap, wnode, inter, beta, mid, r)
                binarySearch(weights, queried, bcap, wnode, inter, beta, l, mid)
            else:
                val = (bcap[upperbound]+bcap[lowerbound]) / 2
                    # print(val)
                    # print(upperbound)
                    # print(wnode[upperbound])
                    # print(lowerbound)
                    # print(wnode[lowerbound])
                for i in range(l, r):
                    inter[i] = val
                for i in range(l, r+1):
                    wnode[i] = val
        elif isninf(bcap[upperbound]) and isninf(bcap[lowerbound]):
            pass
        else:
            # if wnode[l] <= beta + wnode[r] and isninf(wnode[l]):
            #     wnode[l] = wnode[r]
            mid = int((l + r) / 2)
            binarySearch(weights, queried, bcap, wnode, inter, beta, mid, r)
            binarySearch(weights, queried, bcap, wnode, inter, beta, l, mid)
    


def adawish(fp, beta):
    global adaQueryCnt
    adaQueryCnt = 0
    ninf = float('-inf')
    with open(fp, 'r') as f:
        lines = f.readlines()
        nbvar = int(lines[0].split()[0])
        weights = []
        for i in range(1, len(lines)):
            weights.append(float(lines[i].split()[0]))

        # reverMax = weights[-1]
        # i = len(weights) - 2
        # while i > 0:
        #     if weights[i] > reverMax:
        #         reverMax = weights[i]
        #     elif weights[i] == float('-inf'):
        #         weights[i] = reverMax
        #     i -= 1

        # for i in range(len(weights), nbvar):
        #     weights.append(weights[-1])
        # print(weights)
        wnode = [ninf] * (nbvar+1)
        bcap = [ninf] * (nbvar+1)
        interval = [ninf] * nbvar
        queried = [False] * (nbvar+1)
        nbbar = 0
        # wnode[0] = getValue(weights, queried, 0)
        # wnode[-1] = getValue(weights, queried, nbvar)
        binarySearch(weights, queried, bcap, wnode, interval, beta, 0, nbvar)
        
        reverseMaxVal = ninf
        indItr = nbvar
        while indItr >= 0:
            if wnode[indItr] == ninf:
                wnode[indItr] = reverseMaxVal
            else:
                reverseMaxVal = max(wnode[indItr], reverseMaxVal)
            if indItr > 0:
                if interval[indItr-1] == ninf:
                    interval[indItr-1] = reverseMaxVal
                else:
                    reverseMaxVal = max(interval[indItr-1], reverseMaxVal)
            indItr -= 1

        curmax = wnode[0]
        if curmax == float("-inf"):
            return 0
        print(interval)
        print(wnode)
        print(adaQueryCnt)

        W = pow(10, wnode[-1] - curmax)
        for i in range(nbvar):
            W += pow(10, interval[i]- curmax) * nbbar
            W += pow(10, wnode[i] - curmax)
            nbbar = nbbar * 2 + 1
        
        W = math.log10(W) + curmax
        print("Queries made by adawish = {:d}".format(adaQueryCnt))
        print ("Log10 Partition function by adawish = {:.12f}".format(W))
        return W


markers = ['o', '2', '+', 'D', 'h', '*', 's', 'p', 'x']
linestyles = ['--', '-.', '-', '--', '-.', '-', '-.', ':', '--']
# colors = ['xkcd:chocolate brown', 'orange', 'green', 'white', 'xkcd:salmon pink', 'xkcd:rust orange', 'xkcd:cerulean']
method = ["GroundTruth", "BP", "TRWBP", "MeanField", "HAK", "DIS", "WMC", "WISH", "AdaWISH"]
abbreviations = ["jt","_bp", "trwbp", "mf",  "hak", "_dis", "wmc"]
# method = ["(Loopy) Blief Propagation", "Tree-Reweighted Blief Propagation", "Mean Field", "Junction Tree", "WISH", "AdaWish"]
# abbreviations = ["_bp", "trwbp", "mf", "jt"]

if __name__ == "__main__":
    regrex_nbvar = re.compile(r"var([0-9]+)")
    regrex_cplst = re.compile(r"w([0-9.]+)")
    regrex_repeat = re.compile(r"w[0-9.]+_([0-9]+)_")
    regrex_token = []
    for abbr in abbreviations:
        regrex_token.append(re.compile(abbr))
    xs = [[] for i in method]
    ys = [[] for i in method]
    qs = [[], []]
    for file in sorted(os.listdir(args.dir)):
        print(file)
        hasFoundMethod = False
        for index in range(len(abbreviations)):
            if hasFoundMethod:
                break
            if regrex_token[index].search(file) != None:
                hasFoundMethod = True
                # get y axis plot data
                f = open(args.dir+file, 'r')
                res = float(f.readlines()[0])
                f.close()
                ys[index].append(res)

                # get x axis plot data
                if args.xAxis == 0:
                    nbvar = int(regrex_nbvar.search(file).group(1))
                    xs[index].append(nbvar)
                elif args.xAxis == 1:
                    coupling = float(regrex_cplst.search(file).group(1))
                    xs[index].append(coupling)
                else:
                    pass
        if not hasFoundMethod:
            ys[-2].append(wish(args.dir+file))
            nbvar = int(regrex_nbvar.search(file).group(1))
            qs[-2].append((nbvar+1) * T(nbvar))
            ys[-1].append(adawish(args.dir+file, beta))
            qs[-1].append(adaQueryCnt * T(nbvar))

            # get x axis plot data
            if args.xAxis == 0:
                nbvar = int(regrex_nbvar.search(file).group(1))
                xs[-2].append(nbvar)
                xs[-1].append(nbvar)
            elif args.xAxis == 1:
                coupling = float(regrex_cplst.search(file).group(1))
                xs[-2].append(coupling)
                xs[-1].append(coupling)
            else:
                pass
    



    for mind in range(len(method)):
        data_len = -1
        if method[mind] == "GroundTruth":
            data_len = 8
            continue
        elif method[mind] == "HAK":
            data_len = 6
        else:
            data_len = 11
        # print(xs)
        # print(ys[mind][curInd[mind]:curInd[mind]+data_len])
        plt.plot(xs[mind], ys[mind], marker=markers[mind], linestyle=linestyles[mind])
        # curInd[mind] += data_len
    # plt.legend(method)
    jtind = method.index("GroundTruth")
    plt.plot(xs[jtind], ys[jtind], marker=markers[jtind], linestyle=linestyles[jtind], label=method[jtind])
    plt.xlabel("#Variables",size=20)
    plt.ylabel("Log Partition Estimation",size=20)
    plt.xticks(xs[-2], xs[-2])
    plt.legend(fontsize=20)
    plt.tick_params(labelsize=20)
    plt.savefig("/tmp/cliqueestimation.pdf")

    plt.figure()
    plt.tick_params(labelsize=20)
    plt.xlabel("#Variables",size=20)
    plt.ylabel("#MAP Queries(x10^3)",size=20)
    plt.xticks(xs[-2], xs[-2])

    qs = np.array(qs,dtype=np.float64)
    qs = np.true_divide(qs,1000)

    plt.bar(xs[-2], qs[-2], width=1.6, label="WISH")
    plt.bar(xs[-1], qs[-1], width=1.6, label="AdaWISH")
    plt.savefig("/tmp/clique_qry.pdf")
    queryRateArr = np.divide(qs[-1], qs[-2])
    print(queryRateArr)
    print(np.median(queryRateArr))
    print(np.average(queryRateArr))
