#!/bin/bash

#PBS -j oe                                           
#PBS -N ace_isingss
#PBS -q yexiang

set -x
module load utilities parafly
cd $PBS_O_WORKDIR 

datadir=$HOME/adawish/data/isingModel
bindir=$HOME/ace_v3.0_linux86.tar.gz
outdir=$HOME/adawish/output
#uai_file

#seed
#mem
#outputfile



cp $bindir $TMPDIR


cd $TMPDIR

# unzip ace_v3.0_linux86.zip
tar -xzvf ace_v3.0_linux86.tar.gz
cp ins.uai ace_v3.0_linux86

cd ace_v3.0_linux86

ACEDIR=$TMPDIR/ace_v3.0_linux86
cp $datadir/* $ACEDIR/
cp $HOME/adawish/src/aceAly.txt $ACEDIR/
C2D=c2d_linux
export LD_LIBRARY_PATH=$ACEDIR
export ACEDIR=$ACEDIR
export C2D=$C2D
echo "0" > empty.uai.evid
ParaFly -c aceAly.txt -CPU 12 -failed_cmds rerun.txt
cp rerun.txt $HOME/adawish/output/
# java -DACEC2D="$ACEDIR/$C2D" -Xmx${mem}m -classpath "$ACEDIR/ace.jar:$ACEDIR/inflib.jar:$ACEDIR/jdom.jar" mark.reason.apps.BnUai08 -z ins.uai empty.uai.evid $seed > output_file 2>stat_file

# cp output_file $outdir/$outputfile
# cp stat_file $outdir/$outputfile.stat

#cp ins.uai $homedir/$outputfile.uai
