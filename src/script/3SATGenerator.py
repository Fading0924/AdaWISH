import os
import sys
import argparse
import numpy as np
# https://github.com/RalfRothenberger/Power-Law-Random-SAT-Generator
parser = argparse.ArgumentParser(description='Generate random 3SAT instance dataset')

parser.add_argument('-n', type=int, help="number of instances generated for a given dataset")
parser.add_argument('-k', type=int, help="clauses length", default=3)
parser.add_argument('-p', type=float, help="power-law exponent of variables", default=2.5)
parser.add_argument('-b', type=float, help="double power-law exponent of variables")
parser.add_argument('-f', type=str, help="output file path")
parser.add_argument('-u', type=int, help=""'"1"'" for unique varibles in a single clause, 0 otherwise")
args = parser.parse_args()

def generator(nbv, nbc, dir):
    for i in range(args.n):
        file_name = "{}/random3sat_var{:d}_c{:d}_no{:d}".format(dir, nbv, nbc, i)
        command_string = "./CreateSAT -g p -v {} -c {} -k {} -p {} -f {} -u {}".format(
                                nbv, nbc, str(args.k), str(args.p), file_name, str(args.u))
        try:
            os.system(command_string)
        except:
            sys.exit(1)


if __name__ == "__main__":
    variables = [5*i for i in range(1, 11)]
    clauses = [1 for i in variables]
    with open("configure", "w+") as f:
            f.write(str(args))
    for i in range(len(variables)):
        dir_name = "v{}c{}".format(variables[i], clauses[i])
        try:
            os.stat(dir_name)
        except:
            os.mkdir(dir_name)
        generator(variables[i], clauses[i], dir_name)
