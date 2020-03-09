import os
import random
import argparse
import time
datadir = "../data/"
parser = argparse.ArgumentParser(description="Walks through the data folder and triggers parafly script")
parser.add_argument("-d", type=str, default=datadir, help="dataset folder")
parser.add_argument('-l', type=str, default='file', help="Division level of jobs")
parser.add_argument('-o', type=str, default='../output/')
args = parser.parse_args()

def walkandInvoke(fp):
    for file in sorted(os.listdir(fp)):
        if args.l == 'file':
            os.system("python runSlurm.py {} {}".format(args.d+'/'+file, args.o))
        elif args.l == 'depth':
            os.system("python runSlurm_cl.py {} {}".format(args.d+'/'+file, args.o))
        # time.sleep(1000)
if __name__ == "__main__":
    walkandInvoke(args.d)
#     print(args.d)
