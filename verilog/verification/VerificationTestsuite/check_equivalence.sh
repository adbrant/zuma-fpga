#find the folder of this file and place the path in dir

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"


# include base and VTR directories
ZUMA_DIR=$(readlink -f $DIR/../../..)
. $ZUMA_DIR/toolpaths
pwd

YOSYS_DIR=/home/xoar/Projects/yosys


#run yosis and abc
$YOSYS_DIR/yosys -s specification.ys
$YOSYS_DIR/yosys -s removeports.ys
$VTR_DIR/abc/abc -c "cec abc_out_v.blif test.blif"
