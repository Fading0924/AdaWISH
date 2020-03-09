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
plt.rcParams.update({'font.size': 20})
adaQueryCnt = 0
c = 2
beta = math.log10(100)

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
    # print("query depth = {}, res = {}".format(index, mlist[index]))
    adaQueryCnt += 1
    queried[index] = True
    return mlist[index]

def binarySearch(weights, queried, bcap, wnode, inter, beta, l, r):
    # print("Binary Search left={}, right={}".format(l, r))
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
        #     elif weightsplt.style.use('ggplot')[i] == float('-inf'):
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
        # print(interval)
        # print(wnode)
        # print(adaQueryCnt)

        W = pow(10, wnode[-1] - curmax)
        for i in range(nbvar):
            W += pow(10, interval[i]- curmax) * nbbar
            W += pow(10, wnode[i] - curmax)
            nbbar = nbbar * 2 + 1
        
        W = math.log10(W) + curmax
        # print("Queries made by adawish = {:d}".format(adaQueryCnt))
        # print ("Log10 Partition function by adawish = {:.12f}".format(W))
        return W


markers = ['o', '2', '+', 'D', 'h', '*', 's', 'p', 'x']
linestyles = ['--', '-.', '-', '--', '-.', '-', '-.', ':', '--']
# colors = ['xkcd:chocolate brown', 'orange', 'green', 'white', 'xkcd:salmon pink', 'xkcd:rust orange', 'xkcd:cerulean']
method = ["GroundTruth", "BP", "TRWBP", "MeanField", "HAK", "DIS", "WMC", "WISH", "AdaWISH"]
abbreviations = ["_jt_PR","_bp_PR", "_trwbp_PR", "_mf_PR",  "_hak_PR", "_dis_PR", "_wmc_PR", "", ""]
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
    files = []
    for sfile in sorted(os.listdir("/home/vegw/Documents/adawish/data-uai")): 
        print(sfile)
        file = os.path.splitext(sfile)[0]
        files.append(file)
        print(file)

        for index in range(len(abbreviations)):
            res = 0
            fn = "/home/vegw/Documents/adawish/log/UAI/{}".format(file+abbreviations[index])
            if index != method.index("WISH") and index != method.index("AdaWISH"):
                try:
                    f = open(fn, 'r')
                    res = float(f.readlines()[0])
                    f.close()
                except:
                    print("read {} fail".format(file+abbreviations[index]))
                    res = float('-inf')
            elif index == method.index("WISH"):
                res = wish(fn)
                qs[-2].append(int(regrex_nbvar.search(file).group(1))+1)
            else:
                res = adawish(fn, beta)
                qs[-1].append(adaQueryCnt)
            ys[index].append(res)
    
    x = [i for i in range(len(ys[-1]))]
    gtind = method.index("GroundTruth")
    
    print(ys)
    for i in range(len(method)):
        print(len(ys[i]))
        if i == gtind:
            continue
        for j in range(len(x)):
                ys[i][j] -= ys[gtind][j]
                # if ys[i][j] == float("-inf"):
                #     ys[i][j] = 0
    # print(ys)

    
    xs = []
    for i in range(len(x)):
        if i % 2 ==1:
            xs.append(" ")
        elif i < 26:
                xs.append(chr(i+ord('a')))
        else:
            xs.append(chr(i+ord('A')-26))
    print(xs)
    
    # print(files)
    # print(ys[-1])
    for i in range(len(x)):
        ys[gtind][i] = 0

    perm = []
    with open("/tmp/tt.txt", 'r') as f:
        names = []
        for line in f.readlines():
            sfn = re.sub(r'\n','',line)
            sfn = re.sub(r' ','',sfn)
            print(sfn)
            perm.append(files.index(sfn))
    # print(perm)
    # files.index(["Grids_var100f1", "233"])
    files = np.array(files)
    
    newMatrix = np.vstack((files,ys,qs))
    newMatrix[:,[i for i in range(32)]] = newMatrix[:,perm]
    # print (newMatrix)
    files = newMatrix[0,:]
    ys = newMatrix[[i for i in range(1,10)],:].astype(float)
    qs = newMatrix[[-2,-1],:] .astype(int)
    
    qs = qs * 10
    fig = plt.figure(figsize=(8,6))
    ax = fig.add_subplot(111)
    plt.ylabel("Log Partition Estimation Err",fontsize=20)

    plt.ylim(-1, 80)
    plt.xticks(x, xs, fontsize=20)
    plt.xlabel("files", fontsize=20)
    import numpy as np
    for i in range(len(method)):
        if not i == gtind:
                ax.plot(x, np.abs(ys[i]), linestyle=linestyles[i], marker=markers[i], linewidth=2, label=method[i])

    handles, labels = ax.get_legend_handles_labels()
    fig.savefig("UAIestimation.pdf")
    fig_elegend = plt.figure(figsize=(2.3,3.5))
    leg = fig_elegend.legend(handles, labels, loc='center', prop={'size': 18}, ncol=1)
    fig_elegend.savefig("/tmp/est_legend.pdf")
    plt.figure()
    qs = np.array(qs, dtype=np.float64)
    qs = qs / 1000
    plt.bar(x, qs[-2], label="WISH")
    plt.bar(x, qs[-1], label="AdaWISH")

    
    # newMatrix[]
    # qs = qs.astype(int)
    queryRateArr = np.divide(qs[-1], qs[-2])
    print(queryRateArr)
    print(np.median(queryRateArr))
    print(np.average(queryRateArr))

    plt.xticks(x, xs)
    plt.xlabel("files",fontsize=20)
    plt.ylabel("#MAP Queries(x10^3)",fontsize=20)
    # plt.legend()
    plt.savefig("UAIquery.pdf")