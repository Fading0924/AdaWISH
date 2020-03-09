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
c = 5
beta = math.log10(100)
maxdepth = 0
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

def binarySearch(weights, queried, bcap, wnode, inter, beta, l, r, curDepth):
    print("Binary Search left={}, right={}".format(l, r))
    def isninf(a):
        return a == float('-inf')
    global maxdepth
    maxdepth = max(maxdepth, curDepth)
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
                binarySearch(weights, queried, bcap, wnode, inter, beta, mid, r, curDepth+1)
                binarySearch(weights, queried, bcap, wnode, inter, beta, l, mid, curDepth+1)
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
            binarySearch(weights, queried, bcap, wnode, inter, beta, mid, r, curDepth+1)
            binarySearch(weights, queried, bcap, wnode, inter, beta, l, mid, curDepth+1)
    


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
        global maxdepth
        maxdepth = 0
        binarySearch(weights, queried, bcap, wnode, interval, beta, 0, nbvar, 1)
        print(wnode)
        print("maxdepth:{}".format(maxdepth))
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
                try:
                    res = float(f.readlines()[0])
                except:
                    res = float('-inf')
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
            print(file)
            print("wish")
            ys[-2].append(wish(args.dir+file))
            qs[-2].append(int(regrex_nbvar.search(file).group(1))+1)
            ys[-1].append(adawish(args.dir+file, beta))
            qs[-1].append(adaQueryCnt)

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
    

    standLen = len(ys[-1])
    for i in range(len(ys)):
        for j in range(len(ys[i]), standLen):
            ys[i].append(float("-inf"))
            xs[i].append(xs[-1][j])
        print(len(ys[i]))
        
    # print(ys[4])
    # print(ys[5])

    if args.experiment == 1:
        ys = np.array(ys)
        # print(ys.shape)
        xs = np.array(xs)
        ys = ys.reshape(len(method), -1, 10)
        # print(ys)
        # print(ys[4])
        # print(ys[5])
        for i in range(len(method)):
            if i != args.groundtruth:
                ys[i] -= ys[args.groundtruth]
        ys[args.groundtruth] -=  ys[args.groundtruth]
        # print(ys[4])
        # print(ys[5])
        # ys = np.abs(ys)
        ys = np.median(ys, axis=2)
        # print(ys)
        xs = xs.reshape(len(method), -1, 10)[:,:,0]
        ys = np.abs(ys)
        # print(ys)
        # print(xs)
    

    print(ys)
    # ys[method.index("DIS")] /= 10
    # calculation for diff
    gtind = method.index("GroundTruth")
    # whind = method.index("WISH")
    # gtlen = len(xs[gtind])
    # whlen = len(xs[whind])
    # xs[gtind] = xs[whind]
    # for i in range(gtlen, whlen):
    #     ys[gtind].append(ys[whind][i])
    # for i in range(len(xs)):
    #     if i == gtind:
    #         continue
    #     for j in range(len(xs[i])):
    #             ys[i][j] -= ys[gtind][j]
    # for i in range(whlen):
    #     ys[gtind][i] = 0
    # ys = np.abs(ys)
    # mfind = method.index("MeanField")
    # ys[mfind] = -ys[mfind]
    # hakind = method.index("HAK")
    # ys[hakind] = -ys[hakind]

    qs = np.array(qs)
    qs = qs.reshape(2, -1, 10)
    qs = np.median(qs, axis=2)
    
    qs = qs * 10
    # print(qs.shape)
    # print(ys.shape)
    # newMatrix = np.vstack((ys,qs))
    # print(newMatrix)
    # perm = [10,0,1,2,3,4,5,6,7,8,9,11,12,13]
    # newMatrix[:,[i for i in range(14)]] = newMatrix[:,perm]
    # print (newMatrix)
    # files = newMatrix[0,:]
    # ys = newMatrix[[i for i in range(0,10)],:].astype(float)
    # qs = newMatrix[[-2,-1],:] .astype(int)

    fig = plt.figure()
    # plt.subplots_adjust(left=0, bottom=0, right=0.1, top=0.1)
    ax = fig.add_subplot(111)
    for i in range(len(xs)):
        if not i == gtind:
        # if i == method.index("Ace"):
            # ax.plot([5 * i for i in range(1,15)], ys[i], linestyle=linestyles[i],marker=markers[i], linewidth=2, label=method[i])
            ax.plot(xs[i], ys[i], linestyle=linestyles[i],marker=markers[i], linewidth=2, label=method[i])
    
    plt.ylim(-1, 50)
    plt.ylabel("Log Partition Estimation Err")
    if args.xAxis == 0:
        plt.xlabel("#Variables")
    elif args.xAxis == 1:
        plt.xlabel("Coupling strength")
    legend_list = []
    for i in method:
        if i != "GroundTruth":
            legend_list.append(i)
    # plt.legend(legend_list)
    handles, labels = ax.get_legend_handles_labels()
    
    handles = handles[:5] + handles[6:]
    labels = labels[:5] + labels[6:]
    # print(handles)
    fig.savefig("/tmp/estimation.pdf")
    fig_elegend = plt.figure(figsize=(2.3,3.5))
    leg = fig_elegend.legend(handles, labels, loc='center', prop={'size': 18}, ncol=1)
    # leg.get_frame().set_linewidth(0.0)
    fig_elegend.savefig("/tmp/est_legend.pdf")
    fig2 = plt.figure()
    ax2 = fig2.add_subplot(111)
    print(qs)
    qs = np.array(qs, dtype=np.float64)
    qs = np.true_divide(qs,1000)
    # plt.xlim(-0.2, 3.5)
    # plt.ylim(0, 130)
    ax2.bar(xs[-2], qs[-2], width=0.2, label="WISH")
    ax2.bar(xs[-1], qs[-1], width=0.2, label="AdaWISH")
    # ax2.bar([5 * i for i in range(1,15)], qs[-2], width=3, label="WISH")
    # ax2.bar([5 * i for i in range(1,15)], qs[-1], width=3, label="AdaWISH")
    # plt.legend(["WISH", "AdaWish"])
    plt.ylabel("#MAP Queries(x10^3)")
    if args.xAxis == 0:
        plt.xlabel("#Variables")
    elif args.xAxis == 1:
        plt.xlabel("Coupling strength")
    handles, labels = ax2.get_legend_handles_labels()
    fig2.savefig("/tmp/query.pdf")
    fig_qlegend = plt.figure(figsize=(2.3,3.5))
    leg2 = fig_qlegend.legend(handles, labels, loc='center', prop={'size': 18}, ncol=1)
    # leg.get_frame().set_linewidth(0.0)
    fig_qlegend.savefig("/tmp/qry_legend.pdf")
    fig2.savefig("/tmp/query.pdf")

    queryRateArr = np.divide(qs[-1], qs[-2])
    print(queryRateArr)
    print(np.median(queryRateArr))
    print(np.average(queryRateArr))