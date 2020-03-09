import os
import sys
import math
import matplotlib
import re
import numpy as np
matplotlib.use("Agg")
import matplotlib.pyplot as plt 
plt.rcParams.update({'font.size': 14})
adaQueryCnt = 0
c = 2
beta = np.log10([8, 256]).tolist()
def wish(fp):
    with open(fp, 'r') as f:
        lines = f.readlines()
        nbvar = int(lines[0].split()[0])
        weights = []
        for i in range(1, len(lines)):
            weights.append(float(lines[i].split()[0]))
        # for i in range(len(weights), nbvar):
        #     weights.append(weights[-1])
        print(weights)
        curmax = weights[0]
        W = 1
        nbbar = 1
        for i in range(1, nbvar):
            W += pow(10, weights[i] - curmax) * nbbar
            nbbar = nbbar * 2
        
        W = math.log10(W) + curmax
        print("Queries made by wish = {:d}".format(nbvar+1))
        print ("Log10 Partition function by wish = {:.12f}".format(W))
        return W

def getValue(mlist, queried, index):
    if queried[index]:
        return mlist[index]
    global adaQueryCnt
    print("query depth = {}".format(index))
    adaQueryCnt += 1
    queried[index] = True
    return mlist[index]

def binarySearch(weights, queried, wnode, inter, beta, l, r):
    if r == l + 1:
        inter[l] = (wnode[l] + wnode[r]) / 2
    elif wnode[l] <= beta + wnode[r]:
        upperbound = max(l - c, 0)
        lowerbound = min(r + c, len(wnode) - 1)
        wnode[upperbound] = getValue(weights, queried, upperbound)
        wnode[lowerbound] = getValue(weights, queried, lowerbound)
        val = (wnode[upperbound]+wnode[lowerbound]) / 2
        # print(val)
        # print(upperbound)
        # print(wnode[upperbound])
        # print(lowerbound)
        # print(wnode[lowerbound])
        for i in range(l, r):
            inter[i] = val
        for i in range(l + 1, r):
            wnode[i] = val
    else:
        mid = int((l + r) / 2)
        wnode[mid] = getValue(weights, queried, mid)
        binarySearch(weights, queried, wnode, inter, beta, l, mid)
        binarySearch(weights, queried, wnode, inter, beta, mid, r)
    


def adawish(fp, beta):
    with open(fp, 'r') as f:
        lines = f.readlines()
        nbvar = int(lines[0].split()[0])
        weights = []
        for i in range(1, len(lines)):
            weights.append(float(lines[i].split()[0]))
        # for i in range(len(weights), nbvar):
        #     weights.append(weights[-1])
        # print(weights)
        wnode = [0] * (nbvar+1)
        interval = [0] * nbvar
        queried = [False] * (nbvar+1)
        nbbar = 0
        wnode[0] = getValue(weights, queried, 0)
        wnode[-1] = getValue(weights, queried, nbvar)
        binarySearch(weights, queried, wnode, interval, beta, 0, nbvar)
        curmax = wnode[0]
        # print(interval)
        W = pow(10, wnode[-1] - curmax)
        for i in range(nbvar):
            W += pow(10, interval[i]- curmax) * nbbar
            W += pow(10, wnode[i] - curmax)
            nbbar = nbbar * 2 + 1
        
        W = math.log10(W) + curmax
        print("Queries made by adawish = {:d}".format(adaQueryCnt))
        print ("Log10 Partition function by adawish = {:.12f}".format(W))
        return W

if __name__ == "__main__":
    num = re.compile(r"[0-9]+")
    fp = "../log/ising/"
    wish_results = []
    adawish8_results = []
    adawish256_results = []
    wish_query = []
    adawish8_query = []
    adawish256_query = []
    x2 = [5*i for i in range(2,7)]
    x = [5*i for i in range(2,7)]
    acc = [3.103350994428417, 1.7652728629461838, 0.5172151969184962, 0.34496041495995755, 0.31369560585083056]
    
    for file in sorted(os.listdir(fp)):
        wish_results.append(wish(fp+file))
        adaQueryCnt = 0
        adawish8_results.append(adawish(fp+file, beta[0]))
        adawish8_query.append(adaQueryCnt)
        adaQueryCnt = 0
        adawish256_results.append(adawish(fp+file, beta[1]))
        adawish256_query.append(adaQueryCnt)
        nbvar = int(num.search(file).group(0))
        wish_query.append(nbvar+1)


    plt.xlabel("size")
    plt.ylabel("log10 partition function estimate")
    gt = plt.plot(x2, acc, c='r',linestyle='-.', linewidth=2, marker='^', markersize=8)
    wish_e = plt.plot(x, wish_results, c='g',linestyle='--', linewidth=2,marker='o', markersize=7)
    adawish8_e = plt.plot(x, adawish8_results, c='b',linestyle=':',linewidth=2,marker='*', markersize=7)
    adawish256_e = plt.plot(x, adawish256_results, c='m',linestyle=':',linewidth=2,marker='*', markersize=7)
    plt.legend(['ground truth', 'WISH', 'AdaWish-beta8', 'AdaWish-beta256'])
    plt.savefig("/tmp/estimate.png")
    
    fig2 = plt.figure()
    plt.ylim(0, 60)
    wid = 1.5
    x3 = [i-wid for i in x]
    x4 = [i+wid for i in x]
    plt.ylabel("#query")
    plt.xticks(np.arange(10, 50, 5))
    wish_nbquery = plt.bar(x3, wish_query, width=wid, align="center", color="g", label="WISH", alpha=0.5)
    adawish8_nbquery = plt.bar(x, adawish8_query, width=wid, align="center", color="b", label="AdaWish-beta8", alpha=0.5)
    adawish256_nbquery = plt.bar(x4, adawish256_query, width=wid, align="center", color="m", label="AdaWish-beta256", alpha=0.5)
    for bar in wish_nbquery+adawish8_nbquery+adawish256_nbquery:
        h = bar.get_height()
        plt.text(bar.get_x()+wid/2,h, str(h), ha='center', va='bottom' )
    
    plt.legend(loc='upper left', bbox_to_anchor=(0, 1))
    plt.savefig("/tmp/fig.png")
