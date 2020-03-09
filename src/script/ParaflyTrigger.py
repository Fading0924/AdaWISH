import os
import random
import argparse
datadir = "../data/isingModel"
parser = argparse.ArgumentParser(description="Walks through the data folder and triggers parafly script")
parser.add_argument("-d", type=str, default=datadir, help="dataset folder")
parser.add_argument('-l', type=str, default='file', help="Division level of jobs")
args = parser.parse_args()

def walkandInvoke(fp):
    for file in sorted(os.listdir(fp)):
        # print(file)
        # print("python parafly.py {} ../output".format(datadir+'/'+file))
        if args.l == 'file':
            os.system("python parafly.py {} ../output".format(args.d+'/'+file))
        elif args.l == 'depth':
            os.system("python parafly_cl.py {} ../output".format(args.d+'/'+file))
if __name__ == "__main__":
    walkandInvoke(args.d)
#     print(args.d)
