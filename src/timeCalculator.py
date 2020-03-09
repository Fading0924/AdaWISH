import os
import sys
import re
import math
import argparse
import numpy as np
from heapq import *
import time

parser = argparse.ArgumentParser("Time Calculator")
parser.add_argument('-d', '--dir', type=str, default="/tmp/gridising_mixed_field0.1/output/gridising_1_var100_w0.1_0", help="target folder")
parser.add_argument('-g', '--guarantee', type=bool, default=True, help="target folder")
parser.add_argument("-t", '--timeout', type=float, default=0, help="default timeout for MAP queries")
parser.add_argument("-w", '--workers', type=int, default=96, help="number of available cores")
args = parser.parse_args()
beta = 5


def getT(nbr_var, depth):
    # print("get depth:{:d}".format(depth))
    if depth == 0:
        return 1
    intermediate = math.sqrt(pow(2, 5))
    k = intermediate - 1 / intermediate
    prob = 1 - 1 / pow(k, 2)
    alpha = math.log(2) * ((prob - 0.5) ** 2) / (2 * prob)
    T = int(math.ceil(math.log(nbr_var) * math.log(1.0 / 0.01) / alpha))
    if not args.guarantee:
        T = 10
    # print("Value of T:" + str(T))
    return T


def parseFolderName():
    folder_path = os.path.abspath(args.dir)
    print("Target folder path: " + folder_path)
    folder_name = os.path.split(folder_path)[-1]
    print("Target folder : " + folder_name)
    nbr_var = re.search(r'var([0-9]+)', folder_name).group(1)
    print("Number of variables: " + nbr_var)
    nbr_var = int(nbr_var)
    return nbr_var


def wish(nbr_var):
    folder_path = os.path.abspath(args.dir)
    folder_name = os.path.split(folder_path)[-1]

    total_time = 0
    nbr_cores = args.workers
    default_timeout = args.timeout
    h = []

    # for logfile in sorted(os.listdir(args.dir)):
    for depth in range(nbr_var + 1):
        T = getT(nbr_var, depth)
        for i in range(1, T + 1):
            logfile = "{}.xor{:d}.loglen0.{}.ILOGLUE.uai.LOG".format(folder_name, depth, i)
            # print(logfile)

            cost = 0
            logfile_path = "{}/{}".format(args.dir, logfile)
            if not os.path.exists(logfile_path):
                cost = default_timeout
            else:
                with open("{}/{}".format(args.dir, logfile), 'r') as f:
                    lines = f.read()
                    # cost = re.search('Total', lines)
                    cost = re.search(r'Total \(root\+branch&cut\) =[ ]*([0-9.]+)[ ]*sec. \([0-9.]+ ticks\)',
                                     lines).group(1)
                    cost = float(cost)
                    # print(cost)

            if len(h) == nbr_cores:
                total_time = heappop(h)
            time_finished = cost + total_time
            heappush(h, time_finished)

    while len(h) != 0:
        total_time = heappop(h)

    print("WISH total time cost: {:.2f}secs".format(total_time))
    return total_time


import threading
import queue

con = threading.Condition()
Q = queue.SimpleQueue()
total_time_adawish = 0


def solver(folder_name, nbr_var, nbr_cores, res, vis, wnode):
    global total_time_adawish
    remain_cnt = 10
    h = []
    # print("ppp")
    while True:
        if con.acquire():
            # print(total_time_adawish)
            # print("9090")
            if remain_cnt == 0:
                print("AdaWISH total time cost: {:.2f}secs".format(total_time_adawish))
                # print(res)
                # print(wnode)
                # print(len(wnode))
                return
            if Q.empty() and len(h) == 0:
                # print("2323")
                remain_cnt -= 1
                con.wait(1)
            else:
                # print(len(h) < nbr_cores and not Q.empty())
                while len(h) < nbr_cores and not Q.empty():
                    depth, num, cost, value = Q.get()
                    # print("get task: depth={:d}, num={:d}".format(depth, num))
                    # kill
                    if cost == -1:
                        return
                    heappush(h, (total_time_adawish + cost, depth, num, value))

                total_time_adawish, depth, num, value = heappop(h)
                # print("9090")
                # print(depth)
                # print(num)
                res[depth][num - 1] = value
                vis[depth][num - 1] = True

                if len(h) > 0:
                    tt, depth, num, value = heappop(h)
                    while len(h) > 0 and tt == total_time_adawish:
                        res[depth][num - 1] = value
                        vis[depth][num - 1] = True
                        tt, depth, num, value = heappop(h)
                    if tt > total_time_adawish:
                        heappush(h, (tt, depth, num, value))
                    else:
                        res[depth][num - 1] = value
                        vis[depth][num - 1] = True
                    con.notify()
            con.release()


def approxQuery(d, T, res, vis, folder_name, wnode, calculated, queried, bcap):
    returned_res = float("-inf")
    while True:
        if con.acquire():
            if not queried[d]:
                for i in range(1, T + 1):
                    logfile = "{}.xor{:d}.loglen0.{}.ILOGLUE.uai.LOG".format(folder_name, d, i)
                    logfile_path = "{}/{}".format(args.dir, logfile)
                    cost = args.timeout
                    logv = float("-inf")
                    if os.path.exists(logfile_path):
                        with open("{}/{}".format(args.dir, logfile), 'r') as f:
                            lines = f.read()
                            # cost = re.search('Total', lines)
                            cost = re.search(r'Total \(root\+branch&cut\) =[ ]*([0-9.]+)[ ]*sec. \([0-9.]+ ticks\)',
                                             lines).group(1)
                            cost = float(cost)
                            # print(cost)
                            entriesoo = re.search("Solution status = Optimal", lines)
                            entries = re.search("Solution value log10lik = ([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)", lines)
                            if entries is not None and entriesoo is not None:
                                # print(entries.group(1))
                                # print(entries.group(2))

                                logv = float(entries.group(1))
                            else:
                                # print(logfile)
                                entries2 = re.findall(
                                    "\n(\s+)(\d+)(\s+)(\d+)(\s+)([-+]?\d+\.\d+)(\s+)(\d+)(\s+)(\s+|[-+]?\d+\.\d+)(\s+)([-+]?\d+\.\d+)",
                                    lines)
                                if entries2:
                                    # find last entry
                                    # print entries2
                                    # print(entries2[-1][-3])
                                    # print("hahaha")
                                    if entries2[-1][-3].isnumeric():
                                        # print "found something " + str(float(entries2[-1][-3]))
                                        logv = float(entries2[-1][-3])
                                    else:
                                        logv = float("-inf")
                                else:
                                    # Inconsistency detected!
                                    entries3 = re.search("No solution in (\d+) backtracks and", lines)
                                    entries4 = re.search("Inconsistency detected!", lines)
                                    entries5 = re.search("Infeasibility row", lines)
                                    entries6 = re.search("Failed to optimize LP", lines)
                                    entries7 = re.search("Infeasible column", lines)

                                    if (
                                            entries3 is not None or entries4 is not None or entries5 is not None or entries6 is not None or entries7 is not None):
                                        # nothing = 34
                                        logv = float("-inf")
                        Q.put((d, i, cost, logv))
                    else:
                        res[d][i - 1] = float("-inf")
                        vis[d][i - 1] = True
                queried[d] = True
                # print("666")
                con.notify()
                con.release()
                continue

            # print("vis[{}]={}".format(d,vis[d]))
            if not calculated[d]:
                finish = True
                # print("888")
                for i in vis[d]:
                    # print(i)
                    finish = finish and i
                if finish:
                    # print("777")
                    values = res[d].copy()
                    while float("-inf") in values:
                        values.remove(float("-inf"))
                    if len(values) == 0:
                        returned_res = float("-inf")
                    else:
                        returned_res = np.median(np.array(values, dtype=np.float64))
                    calculated[d] = True
                    bcap[d] = returned_res
                    # if (d==100):
                    # print("wnode[100]={}".format(bcap[d]))
                    con.release()
                    # print("approxquery:{}-{}".format(d, returned_res))
                    return
            # print("999")
            if calculated[d]:
                # print("sdsds")
                con.release()
                returned_res = bcap[d]
                return
            else:
                con.notify()
                con.release()
                # time.sleep(10)


def binarySearch(l, r, nbr_var, res, vis, folder_name, wnode, calculated, queried, bcap):
    # print("Binarysearch: ({:d},{:d})".format(l, r))
    # if (l ==0 and r == 12):
    #     print("6666")
    def isninf(a):
        return a == float('-inf')

    if r == l + 1:
        # ql = queue.Queue()
        # qr = queue.Queue()
        lt = threading.Thread(target=approxQuery,
                              args=(l, getT(nbr_var, l), res, vis, folder_name, wnode, calculated, queried, bcap))
        rt = threading.Thread(target=approxQuery,
                              args=(r, getT(nbr_var, r), res, vis, folder_name, wnode, calculated, queried, bcap))
        lt.start()
        rt.start()
        lt.join()
        rt.join()
        left_val = bcap[l]
        right_val = bcap[r]
        if not isninf(left_val) and not isninf(right_val):
            wnode[l] = left_val
            wnode[r] = right_val
        else:
            pass
    else:
        upperbound = max(l - 5, 0)
        lowerbound = min(r + 5, len(wnode) - 1)
        # qu = queue.Queue()
        # ql = queue.Queue()
        ut = threading.Thread(target=approxQuery, args=(
        upperbound, getT(nbr_var, upperbound), res, vis, folder_name, wnode, calculated, queried, bcap,))
        lt = threading.Thread(target=approxQuery, args=(
        lowerbound, getT(nbr_var, lowerbound), res, vis, folder_name, wnode, calculated, queried, bcap))
        lt.start()
        ut.start()
        ut.join()
        lt.join()
        # print("({},{})".format(l, r))
        # print("444444444444444444444444444444444")
        upp_val = bcap[upperbound]
        low_val = bcap[lowerbound]
        # print(upperbound)
        # print(lowerbound)
        # print(upp_val)
        # print(low_val)
        if not isninf(upp_val) and not isninf(low_val):
            if upp_val >= beta + low_val:
                # print("4534534")
                mid = int((l + r) / 2)
                t1 = threading.Thread(target=binarySearch,
                                      args=(l, mid, nbr_var, res, vis, folder_name, wnode, calculated, queried, bcap))
                t1.start()
                t2 = threading.Thread(target=binarySearch,
                                      args=(mid, r, nbr_var, res, vis, folder_name, wnode, calculated, queried, bcap))
                t2.start()
            else:
                # print("09090")
                val = (upp_val + low_val) / 2
                for i in range(l, r + 1):
                    wnode[i] = val
                    # if (i == 100):
                    #     print("wnode[100]={}".format(wnode[100]))
                        # print(upp_val)
                        # print(low_val)
                        # print(upperbound)
                        # print(lowerbound)
        elif isninf(upp_val) and isninf(low_val):
            pass
        else:
            mid = int((l + r) / 2)
            # print("googogog")
            t1 = threading.Thread(target=binarySearch,
                                  args=(l, mid, nbr_var, res, vis, folder_name, wnode, calculated, queried, bcap))
            t1.start()
            t2 = threading.Thread(target=binarySearch,
                                  args=(mid, r, nbr_var, res, vis, folder_name, wnode, calculated, queried, bcap))
            t2.start()
    return


def adawish(nbr_var):
    MAP_query_result = [[float('-inf') for i in range(getT(nbr_var, j))] for j in range(nbr_var + 1)]
    MAP_query_visit = [[False for i in range(getT(nbr_var, j))] for j in range(nbr_var + 1)]
    folder_path = os.path.abspath(args.dir)
    folder_name = os.path.split(folder_path)[-1]

    nbr_cores = args.workers
    default_timeout = args.timeout
    wnode = [float('-inf') for i in range(nbr_var + 1)]
    # print(wnode)
    # time.sleep(10)
    calculated = [False for i in range(nbr_var + 1)]
    queried = [False for i in range(nbr_var + 1)]

    bcap = [float('-inf') for i in range(nbr_var + 1)]
    s = threading.Thread(target=solver,
                         args=(folder_name, nbr_var, nbr_cores, MAP_query_result, MAP_query_visit, wnode))
    t = threading.Thread(target=binarySearch, args=(
    0, nbr_var, nbr_var, MAP_query_result, MAP_query_visit, folder_name, wnode, calculated, queried, bcap))
    # print("solver")
    s.start()
    t.start()

    t.join()
    s.join()
    return


if __name__ == '__main__':
    nbr_var = parseFolderName()
    wish_time = wish(nbr_var)
    adawish(nbr_var)
    ratio = total_time_adawish/wish_time
    print("Time ratio: {:2f}%".format(ratio*100))




