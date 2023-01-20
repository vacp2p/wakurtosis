#!/bin/sh

#MAX and MIN for topics and num nodes
MIN=5
MAX=100

#requires bc
getrand(){
  orig=$(od -An -N1 -i /dev/urandom)
  range=`echo "$MIN + ($orig % ($MAX - $MIN + 1))" | bc`
  RANDOM=$range
}

getrand1(){
  orig=$(od -An -N1 -i /dev/urandom)
  range=`echo "$MIN + ($orig % ($MAX - $MIN + 1))" | bc`
  return range
  #getrand1  # call the fun and use the return value
  #n=$? 
}

if [ "$#" -ne 2 ] || [ $2 -le 0 ] ; then
  echo "usage: $0 <output dir> <#json files needed>" >&2
  exit 1
fi

path=$1
nfiles=$2
mkdir -p $path

echo "Ok, will generate $nfiles networks & put them  under '$path'."
 
nwtype="newmanwattsstrogatz"
nodetype="desktop"


for i in $(seq $nfiles)
do
  getrand
  n=$((RANDOM+1))
  getrand 
  t=$((RANDOM+1))
  getrand 
  s=`expr $((RANDOM+1)) % $n`

  dirname="$path/$i/Waku"
  mkdir "$path/$i"
  echo "Generating ./generate_network.py --dirname $dirname --num-nodes $n --num-topics $t --nw-type $nwtype --node-type $nodetype --num-partitions 1 --num-subnets $s ...."
  $(./generate_network.py --dirname $dirname --num-nodes $n --num-topics $t --nw-type $nwtype --node-type $nodetype --num-partitions 1 --num-subnets $s)
done
