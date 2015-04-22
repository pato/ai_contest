#!/bin/bash
if (($# < 1))
then
  echo "Usage ./concur.py NUMGAMES"
  exit 1
fi

for i in `seq 1 $1`;
do
  python2 capture.py -r Dankest -z 0.2 &
done
