#!/bin/bash
#find the folder of this file and place the path in dir

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

echo "---------verification Overlay tests----------------"

cd $DIR

# include base and VTR directories
#ZUMA_DIR=$(readlink -f $DIR/../../..)
#. $ZUMA_DIR/toolpaths
#pwd

#yosys dir is extracted from the toolpath.py
#YOSYS_DIR=/home/xoar/Projects/yosys


#run yosis and abc
$YOSYS_DIR/yosys -s specification.ys
$YOSYS_DIR/yosys -s removeports.ys
$YOSYS_DIR/yosys -s removeports_abc.ys

sequential=$(grep -c -m 1 "^.latch" abc_out_v_opt.blif)

if [ $sequential -eq 0 ]; then
        echo "Found no latches in input circuit: Circuit is combinational"
        echo
        echo "Checking for combinational equivalence with ODINs result:"
        echo -e 'cec abc_out_v_opt.blif test_opt.blif\nquit' | $VTR_DIR/abc/abc
    else
        echo "Found latches in input circuit: Circuit is sequential"
        echo
        echo "Checking for sequential equivalence with ODINs result:"
        echo -e 'dsec abc_out_v_opt.blif test_opt.blif\nquit' | $VTR_DIR/abc/abc
    fi
    echo
