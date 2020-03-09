import os
import sys
import re


fp = "/tmp/cnf/"
pat = re.compile("p cnf ([0-9]+) ([0-9]+)")
for file in sorted(os.listdir(fp)):
    with open(fp+file, 'r') as f:
        haveFoundDeclaration = False
        nbvar = -1
        for line in f.readlines():
            matchRes = pat.search(line)
            print(matchRes.group(0))
            if matchRes is not None:
                nbvar = int(matchRes.group(1))
                haveFoundDeclaration = True
                break
        if not haveFoundDeclaration:
            raise ValueError("CNF file does not have declaration line")

    with open(fp+file, 'a') as f:
        for i in range(1, nbvar+1):
            f.write("w {:d} 1\n".format(i))
            f.write("w -{:d} 1\n".format(i))

            