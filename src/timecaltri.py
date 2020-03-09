import os
import sys

for f in sorted(os.listdir("/tmp/gridising_mixed_field0.1/output/")):
    # print(f)
    # print(os.path.isdir("/tmp/gridising_mixed_field0.1/output/"+f))
    fp = "/tmp/gridising_mixed_field0.1/output/" + f
    if os.path.isdir(fp):
        # print("python timeCalculator.py -d {} 2&1>{}.txt".format(fp, f))
        os.system("python timeCalculator.py -d {}".format(fp, f))