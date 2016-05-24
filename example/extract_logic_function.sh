#find the folder of this file and place the path in dir

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"


# include base and VTR directories
ZUMA_DIR=$(readlink -f $DIR/..)
. $DIR/../toolpaths
pwd

if [[ $# -ne 4 ]]; then
    echo "Illegal number of parameters"
	echo "Usage: extract_logic_function bitstream.mif output.blif HasClock HasReset"
fi

bitfile=$1
bitfile=$(readlink -f $bitfile)

outputfile=$2
outputfile=$(readlink -f $outputfile)

#echo "Synthesizing '$verilogfile' to ZUMA"

#move configuration files to python source folder
cp zuma_config.py $ZUMA_DIR/source/

#we can check if vpr7 or vpr6 is used
#by checking the exit status
$ZUMA_DIR/source/ReadVprVersion
STATUS=$?
echo "output of vpr status was"
echo $STATUS
if [ $STATUS -ne 0 ]; then
    echo "VPR7 is used!"
    export USE_VPR_7=1
else
    echo "VPR7 is not used!"
    export USE_VPR_7=0
fi

#move to build folder to collect build related files
mkdir -p build
cd build

rm abccommands \
   mem.echo \
   rr_graph.echo \
   vpr.sh \
   abc_out.blif \
   configpattern.txt \
   netlist.net \
   seg_details.txt \
   zuma_out_reverse.blif \
   arch.echo \
   config_script.tcl \
   place.p \
   startfile \
   default_out.blif\
   route.r \
   user_clocks.clock

if [ $USE_VPR_7 -eq 0 ]; then
    rm clock_fixed.blif \
       ARCH.xml
#vpr7 is used
else
    rm ARCH_vpr7.xml
fi

touch startfile

#generate vpr architecture and other files needes during build process
python2.7 $ZUMA_DIR/source/generate_buildfiles.py ./ $ZUMA_DIR/source/templates

failed=0

#copy the dummy for the new and old vpr version
cp $DIR/dummy_for_extraction.blif ./abc_out.blif
cp $DIR/dummy_for_extraction.blif ./clock_fixed.blif

#run vpr to create graph.echo
sh vpr.sh || failed=1

echo

if [ "$failed" -eq 1 ]; then
    echo "VPR failed..."
    echo
    exit
fi

#if vpr7 is unset
if [ $USE_VPR_7 -eq 0 ]; then
    #run the zuma generation scripts
    #python $ZUMA_DIR/source/run_zuma_all.py ./ ../generated/
    python2.7 $ZUMA_DIR/source/ZumaBitToBlif.py  \
    -graph_file 'rr_graph.echo' \
    -blif_file $outputfile \
    -mif_file $bitfile \
    -verilog_file 'ZUMA_custom_generated.v' \
    -use_reset $4 \
    -use_clock $3 &&\
    {
        echo
        echo "Success: All done."
    }

#vpr7 is used
else

    #run the zuma generation scripts
    #python $ZUMA_DIR/source/run_zuma_all.py ./ ../generated/
    python2.7 $ZUMA_DIR/source/ZumaBitToBlif.py \
    -graph_file 'rr_graph.echo' \
    -blif_file $outputfile \
    -mif_file $bitfile \
    -verilog_file 'ZUMA_custom_generated.v' \
    -use_reset $4 \
    -use_clock $3 &&\
    {
        echo
        echo "Success: All done."
    }

fi

