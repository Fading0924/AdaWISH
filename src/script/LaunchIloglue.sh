#!/bin/bash
#PBS -j eo

set -x
#module load anaconda/5.3.1-py37
cd $PBS_O_WORKDIR

cp $basedir/../bin/AdaWish $tmpdir/iloglue

cd $tmpdir

timeout $timeout $tmpdir/iloglue -paritylevel 1 -number $level $basedir/$file > out

# Copy output files to your output folder
cp -f $tmpdir/out $basedir/../log/$outdir/`basename $file`.xor$level.loglen$len.$sample.ILOGLUE.uai.LOG
