import sys
import math
import os
import argparse
# from WISHLogProcess import process_logs 
# from WISHLogProcess import process_logs_cplex_LB
# from WISHLogProcess import process_logs_cplex_UB



parser = argparse.ArgumentParser(description='Estimate the partition function using the WISH algorithm and CPLEX for the optimization.')


parser.add_argument("infile", help="Graphical model (in UAI format)")
parser.add_argument("outfolder", help="Folder where logs are stored")
parser.add_argument('-c', type=float, help="Approximate parameter", default=5)
parser.add_argument('-d', '--delta', type=float, help="Failure probability delta", default=0.01)
parser.add_argument('-t', '--timeout', type=int, help="Timeout for each optimization instance (seconds)", default=3600)
parser.add_argument('-q', '--queue', type=str, default="standby", help="qsub queue")
# parser.add_argument('-r', '--repeat', type=int, default=0, help="repeat time counter")
args = parser.parse_args()


print("Reading factor graph from " + args.infile)
inputfile = open(args.infile, "r")

fileName, fileExtension = os.path.splitext(args.infile)

ind = 0
origNbrFactor = 0
origNbrVar = 0
for l in inputfile:
	if not l.strip()=='':
		ind = ind +1
		if ind==2:
			origNbrVar=int(l)
		elif ind==3:
			l = l.rstrip("\n")
		elif ind==4:			## add xor cpt tabe
			origNbrFactor = int(l)
		elif ind>5:
			break
print("Model with " + str(origNbrVar) + " variables and "+str(origNbrFactor) +" factors")

depth = origNbrVar
intermediate = math.sqrt(pow(2,args.c))
k = intermediate - 1 / intermediate
prob = 1 - 1 / pow(k, 2)
alpha = math.log(2) * ((prob - 0.5) ** 2) / (2 * prob)
# T = int(math.ceil(math.log(origNbrVar)*math.log(1.0/args.delta)/alpha))
T = 10
print("Using " + str(T) +" samples per level")

fname_extended = os.path.basename(args.infile)
print(fname_extended)
fname = os.path.splitext(fname_extended)[0]
outputdir = args.outfolder+'/'+fname+'/'
basedir = os.path.dirname(os.path.abspath('./'))
filedir = os.path.abspath(os.path.split(args.infile)[0])
curdir = os.path.dirname(os.path.abspath('__file__'))
if not os.path.exists(outputdir):
	os.system("mkdir "+ outputdir)
parafileName = "%s_script.txt" % (fname)
rerunfile = "%s/%s" % (outputdir, "rerun.txt")
if  os.path.exists(rerunfile): # all instances finished
	sys.exit(0)
f = open(parafileName, 'w')
lineCnt = 0
for i in range(0,depth+1):			## main for loop
	if i==0:
		sampnum=1
	else:
		sampnum=T
	for t in range(1,sampnum+1):			## main for loop
		outfilenamelog = "%s.xor%d.loglen%d.%d.ILOGLUE.uai.LOG" % (fname, i , 0 , t)
		targetfile = "%s/%s" % (outputdir, outfilenamelog)
		if not os.path.exists(targetfile):
			# print(targetfile)
			# sys.exit(0)
			lineCnt += 1
			cmdline = ("timeout %d ./ilog -timelimit %d -paritylevel 1 -number %d %s > %s && cp %s %s") % (args.timeout , 900, i , fname_extended , outfilenamelog, outfilenamelog, outputdir)
			f.write(cmdline+'\n')
		## Parallel execution:
		##
		## assign this job to a separate core (a system dependent script is needed here)
		## we provide an example based on Torque/PBS:
		##
		## os.system("qsub -v basedir="+basedir+",file="+infile+",level="+str(i)+",len="+str(0)+",outdir="+outdir+",sample="+str(t)+",timeout=900s"+" LaunchIloglue.sh")
f.close()
if lineCnt == 0: # all instances finished
	os.system("rm %s" % (parafileName))
	sys.exit(0)
sname = fname+ "Launch.sh"
f = open(sname, 'w')
f.write("#!/bin/bash\n")
f.write("#PBS -j oe\n")
f.write("#PBS -N %s\n" % (fname))
f.write("\n")

f.write("set -x\n")
f.write("cd $PBS_O_WORKDIR\n")
f.write("module load utilities parafly\n")
f.write("basedir={}\n".format(basedir))
f.write("datadir={}\n".format(filedir))
f.write("TMPDIR=/tmp\n")
f.write("cp %s $TMPDIR/\n" % (sname))
f.write("cp %s $TMPDIR/\n" % (parafileName))
f.write("cp $basedir/bin/AdaWish $TMPDIR/ilog\n")
f.write("cp $datadir/%s $TMPDIR/%s\n" % (fname_extended, fname_extended))
f.write("cd $TMPDIR\n")
f.write("ParaFly -c %s_script.txt -CPU 24 -failed_cmds rerun.txt\n" % (fname))
f.write("cp rerun.txt %s" % (curdir+'/'+outputdir))
f.close()

# os.system("qsub -q %s -l walltime=04:00:00,nodes=1:ppn=24 %s" % (args.queue, sname))