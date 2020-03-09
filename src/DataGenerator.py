import os
import random
import math
import time
import argparse
import numpy as np

parser = argparse.ArgumentParser("Generate dataset for AdaWish benckmark")
parser.add_argument('-w', type=float, default=0.1, help="coupling strength")
parser.add_argument('-d', '--dir', type=str, default="../data/isingModel", help="relative path to this python source file")
parser.add_argument('-f', '--field', type=float, default=0.1, help="local field value")
parser.add_argument('-i', '--interaction', type=int, default=0, help="0 for attractive, 1 for mixed")
parser.add_argument('-m', '--model', type=str, default="clique", help="clique-random clique-structured Ising model; grid-grid Ising model")
parser.add_argument('-l', '--length', type=int, default=5, help="length of the inserted closed chain")
parser.add_argument('-n', type=int, default=10, help="grid length")
args = parser.parse_args()

srcdir = os.getcwd()
datadir = srcdir+'/'+args.dir

def getIndex(nbvar, *vars):
    id = 0
    for var in vars:
        id *= nbvar
        id += var
    return id

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def getRandomSubset(sz):
    prob = random.random()
    subset = []
    for i in range(sz):
        if random.random() < prob:
            subset.append(i)
    return subset

def GridIsingModel(fp):
    def getEdgeofNode(length, ind, direction):
        if ind >= length**2 or ind < 0:
            print ("Invalid index {:d}".format(ind))
            return -1
        row = int(ind / length)
        col = ind % length 
        invalid_row_status = [(0,0), (length-1,2)]
        invalid_col_status = [(0,1), (length-1,3)]
        if ((row, direction) in invalid_row_status) or ((col, direction) in invalid_col_status):
            print ("Invalid request for edge index ({:d}, {:d}, {:d})".format(length, ind, direction))
            return -1
        if direction == 2:
            return getEdgeofNode(length, ind+length, 0)
        elif direction == 3:
            return getEdgeofNode(length, ind+1, 1)
        else:
            prev_edge_cnt = 0
            if row == 0:
                prev_edge_cnt = col - 1
            else:
                prev_edge_cnt = (2*length-1)*row - length + max(2*col-1, 0)
            prev_edge_cnt += direction
            return int(prev_edge_cnt)
            
    def printGrid():
        l = args.n
        curRow = 0
        print (interaction)
        while curRow < l:
            print("o", end='')
            eind = 0
            if curRow == 0:
                eind = 0
            else:
                eind = (2*l-1)*curRow - l + 2
            for _ in range(l - 1):
                print("--{:.1f}--o".format(interaction[eind]), end='')
                # print("--{:.1f}--o".format(float(eind)), end='')
                eind += min(curRow+1, 2)
            curRow += 1
            print('\n')
            if curRow >=l:
                return
            eind = (2*l-1)*curRow - l
            
   
            for _ in range(l):
                print('|       ', end='')
            print('\n', end='')
            # print('\n')
            curCol = 0
            for _ in range(l):
                print("{:.1f}     ".format(interaction[eind]), end='')
                # print("{:.1f}     ".format(float(eind)), end='')
                eind += min(curCol+1, 2)
                curCol += 1

            print('\n')
            for _ in range(l):
                print('|       ', end='')
            print('\n')

    # 10 * 10 binary grid Ising model
    l = args.n
    nbvar = l ** 2

    localfield = []
    interaction = []
    functables = []
    nbconstrains = 0
    pos = [-l, -1]
    with open(fp, 'w') as f:
        f.write("MARKOV\n")
        f.write(str(nbvar) + "\n")
        for i in range(nbvar):
            f.write("2 ")
        f.write("\n")
        
        # f.write("{:d}\n".format(3*(l**2)-2*l))
        # for i in range(nbvar):
        #     randlf = (random.random() - 0.5) * 2 * args.field
        #     localfield.append(randlf)
        #     f.write("1 {:d}\n".format(i))
        #     for p in range(len(pos)):
        #         # A valid pair of vars
        #         if (p == 0 and i + pos[p] >= 0) or (p == 1 and i % l + pos[p] >=0):
        #             randit = (random.random() - args.interaction/2) * (args.interaction + 1) * args.w
        #             interaction.append(randit)
        #             f.write("2 {:d} {:d}\n".format(i, i+pos[p]))
        for i in range(nbvar):
            randlf = (random.random() - 0.5) * 2 * args.field
            localfield.append(randlf)
            nbconstrains += 1
            functables.append("1 {:d}\n".format(i))
            for p in range(len(pos)):
                # A valid pair of vars
                if (p == 0 and i + pos[p] >= 0) or (p == 1 and i % l + pos[p] >=0):
                    randit = (random.random() - args.interaction/2) * (args.interaction + 1) * args.w
                    interaction.append(randit)
                    nbconstrains += 1
                    functables.append("2 {:d} {:d}\n".format(i, i+pos[p]))
        # strong structure
        structure_num = 1
        while structure_num < 2:
            # upper left node of rectangle
            upper_left = int(random.random() * nbvar)
            row = int(upper_left / args.n)
            col = upper_left % args.n
            col_len = min(args.n-col-1, int(0.5*args.n))
            row_len = min(args.n-row-1, int(0.5*args.n))
            if col_len == 0 or row_len == 0:
                continue

            for i in range(row_len):
                for j in range(col_len):
                    curInd = upper_left + i * args.n + j
                    if i > 0:
                        eind = getEdgeofNode(args.n, curInd, 0)
                        interaction[eind] = (random.random() - args.interaction/2) * (args.interaction + 1) * args.w * 10
                    if j > 0:
                        eind = getEdgeofNode(args.n, curInd, 1)
                        interaction[eind] = (random.random() - args.interaction/2) * (args.interaction + 1) * args.w * 10
            
        # while structure_num <= args.n:
        #     tedges = random.sample(range(len(interaction)), int(len(interaction)/args.n))
        #     for te in tedges:
        #         interaction[te] = (random.random() - args.interaction/2) * (args.interaction + 1) * args.w * structure_num
            # Amplify Edges along the perimeter of squares
            # steps = [1, l, -1, -l]
            # directions = [3, 2, 1, 0]
            # upper_right = upper_left + col_len
            # lower_left = upper_left + row_len*args.n 
            # lower_right = upper_right + row_len*args.n
            # nodes = [upper_right, lower_right, lower_left, upper_left]
            # print(nodes)
            # curInd = upper_left
            # print("curInd="+str(curInd))
            # for curDir in range(4):
            #     while curInd != nodes[curDir]:
            #         eind = getEdgeofNode(args.n, curInd, directions[curDir])
            #         print("eind="+str(eind))
            #         interaction[eind] = (random.random() - args.interaction/2) * (args.interaction + 1) * args.w * 1e2
            #         curInd += steps[curDir]
            #         print("curDir="+str(curDir))
            #         print("curInd="+str(curInd))
            structure_num += 1
        # printGrid()
        # subsetSize = int(0.2 * nbvar)
        # subset = random.sample(range(0, nbvar), subsetSize)
        # subset = sorted(subset)
        # for i in range(subsetSize):
        #     for j in range(i):
        #         var1 = i
        #         var2 = j
        #         nbconstrains += 1
        #         functables.append("2 {:d} {:d}\n".format(var1, var2))
        #         randit = (random.random() - args.interaction/2) * (args.interaction + 1) * args.w
        #         # print(randit > 100)
        #         interaction.append(randit)

        f.write("{:d}\n".format(nbconstrains))
        for i in range(len(functables)):
            f.write(functables[i])

        cursor = 0
        localfield = np.exp(localfield).tolist()
        # print (interaction)
        interaction = np.exp(interaction).tolist()
        for i in range(nbvar):
            vl = localfield[i]
            f.write("2\n{:.12f}\n{:.12f}\n\n".format(1/vl, vl))
            for p in range(len(pos)):
                # A valid pair of vars
                if (p == 0 and i + pos[p] >= 0) or (p == 1 and i % l + pos[p] >=0):
                    vi = interaction[cursor]
                    cursor += 1
                    f.write("4\n{:.12f}\n{:.12f}\n{:.12f}\n{:.12f}\n\n".format(vi, 1/vi, 1/vi, vi))
            
        for i in range(cursor, len(interaction)):
            vi = interaction[i]
            f.write("4\n{:.12f}\n{:.12f}\n{:.12f}\n{:.12f}\n\n".format(vi, 1/vi, 1/vi, vi))

def RandomCliqueIsingModel(fp, nbvar):
    with open(fp, 'w+') as f:
        f.write("MARKOV\n")
        f.write(str(nbvar) + "\n")
        for i in range(nbvar):
            f.write("2 ")
        f.write("\n")
        
        # 
        # random clique
        constraints_cnt = 0
        funcVars = []
        functable = []
        for i in range(1, nbvar):
            for j in range(0, i):
                constraints_cnt += 1
                # val = math.exp(-1 * random.random() * args.w)
                val = math.exp(-1 * random.random() * args.w * math.sqrt(i - j))
                funcVars.append("2 {:d} {:d}\n".format(i, j))
                # functable.append("{:d}\n{:.12f}\n{:.12f}\n{:.12f}\n{:.12f}\n\n".format(4,
                #     1, val,
                #     val, 1))
                functable.append(val)
        # random repulsive
        
        for structure_now in range(2):
            # closed chain
            subset = random.sample(range(0, nbvar), int(0.3 * nbvar))
            # print(subset)
            random.shuffle(subset)
            # print(subset)
            if len(subset) >= 2:
                for i in range(len(subset)):
                    ind1 = i
                    ind2 = i + 1
                    if ind2 == len(subset):
                        ind2 = 0
                    v1 = max(subset[ind1], subset[ind2])
                    v2 = min(subset[ind1], subset[ind2])
                    index = int(v1 * (v1 - 1) / 2 + v2)
                    amplify_rate = sigmoid((random.random() - 0.5)) * 1e2
                    val = math.exp(random.random() * args.w * amplify_rate)
                    # val = random.random() * args.w * -10
                    # print(str(index) + "/" + str(constraints_cnt))
                    functable[index] += val
        
        # subset = random.sample(range(0, nbvar), 2)
        # # print(subset)
        # random.shuffle(subset)
        # # print(subset)
        # if len(subset) >= 2:
        #     for i in range(len(subset)):
        #         ind1 = i
        #         ind2 = i + 1
        #         if ind2 == len(subset):
        #             ind2 = 0
        #         v1 = max(subset[ind1], subset[ind2])
        #         v2 = min(subset[ind1], subset[ind2])
        #         index = int(v1 * (v1 - 1) / 2 + v2)
        #         val = math.exp(random.random() * args.w * 1e-2)
        #         # val = random.random() * args.w * -10
        #         # print(str(index) + "/" + str(constraints_cnt))
        #         functable[index] += val

        f.write("{:d}\n".format(constraints_cnt))
        for i in range(constraints_cnt):
            f.write(funcVars[i])
        f.write("\n\n")
        for i in range(constraints_cnt):
            val = functable[i]
            f.write("{:d}\n{:.12f}\n{:.12f}\n{:.12f}\n{:.12f}\n\n".format(4, 1, val, val, 1))

            


if __name__ == "__main__":
    if not os.path.exists(datadir):
        os.mkdir(datadir)
        
    with open(datadir+"/args.conf", 'w') as f:
        print(args)

    if args.model == "clique":
        for i in range(11):
            nbvar = 3 * i + 10
            for j in range(10):
                filename = "{}ising_var{:d}_{:d}.uai".format(args.model, nbvar, j)
                RandomCliqueIsingModel(datadir+'/'+filename, nbvar)
    elif args.model == "grid":
        nbvar = args.n ** 2
        for i in range(10):
            filename = "{}ising_{:d}_var{:d}_w{:.1f}_{:d}.uai".format(args.model, args.interaction, nbvar, args.w, i)
            GridIsingModel(datadir+'/'+filename)