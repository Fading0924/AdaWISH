import os
import re
fp = "/home/vegw/Documents/adawish/data-uai"
outputdir="/tmp/DISLOG"
fac = re.compile(r"[+-]?[0-9]+(\.[0-9]+)?")
for file in sorted(os.listdir(fp)):
    for alg in ['dis']:
        fileName = file + "_{}_PR".format(alg)
        outfile = "{}/{}_{}_PR".format(outputdir, os.path.splitext(file)[0], alg)
        if not os.path.exists("LOGS/"+fileName):
            print("    cannot find libDAI output {}, skip".format(fileName))
        else:
            with open("LOGS/"+fileName, 'r') as rf, open(outfile, 'w') as wf:
                print(fileName)
                try:
                    ans = fac.search(rf.readlines()[2]).group(0)
                except:
                    continue
                print(ans)
                wf.write(ans)