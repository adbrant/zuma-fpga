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

#check which file to compile
filename=$1
if [ -z "$filename" ]; then
    filename="test.v"
fi
filename=$(readlink -f $filename)
echo "Synthesizing '$filename' to ZUMA"

#move configuration files to python source folder
cp zuma_config.py $ZUMA_DIR/source/


echo "VPR7 is used!"
export USE_VPR_7=1


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
   zuma_out.blif \
   arch.echo \
   config_script.tcl \
   place.p \
   startfile \
   default_out.blif\
   route.r \
   user_clocks.clock


rm ARCH_vpr8.xml

touch startfile

#generate vpr architecture and other files needes during build process
python2.7 $ZUMA_DIR/source/generate_buildfiles.py ./ $ZUMA_DIR/source/templates

failed=0

#run odin, abc and vpr
$VTR_DIR/ODIN_II/odin_II.exe -V $filename &&\
$VTR_DIR/abc_with_bb_support/abc < abccommands &&\
sh vpr8.sh || failed=1

echo
if [ "startfile" -nt "place.p" ]; then
    echo "Placement failed..."
    failed=1
fi

if [ "startfile" -nt "route.r" ]; then
    echo "Routing failed..."
    failed=1
fi
if [ "$failed" -eq 1 ]; then
    echo "ODIN, ABC or VPR failed..."
    echo
    exit
fi


echo "Take branch VPR used"
#run the zuma generation scripts
#python $ZUMA_DIR/source/run_zuma_all.py ./ ../generated/
python2.7 $ZUMA_DIR/source/zuma_build.py \
-graph_file 'rr_graph.echo' \
-blif_file 'abc_out.blif' \
-place_file 'place.p' \
-route_file 'route.r' \
-net_file 'netlist.net' \
-bit_file '../output.hex' \
-blif_out_file 'zuma_out.blif' \
-verilog_file '../ZUMA_custom_generated.v' &&\
{
    sequential=$(grep -c -m 1 "^.latch" abc_out.blif)

    echo
    echo "Success: All done."
    if [ $sequential -eq 0 ]; then
        echo "Found no latches in input circuit: Circuit is combinational"
        echo
        echo "Checking for combinational equivalence with ODINs result:"
        echo -e 'cec abc_out.blif zuma_out.blif\nquit' | $VTR_DIR/abc_with_bb_support/abc
    else
        echo "Found latches in input circuit: Circuit is sequential"
        echo
        echo "Checking for sequential equivalence with ODINs result:"
        echo -e 'sec abc_out.blif zuma_out.blif\nquit' | $VTR_DIR/abc_with_bb_support/abc
    fi
    echo

    cd ..
    sh $ZUMA_DIR/example/hex2mif.sh output.hex > output.hex.mif

    lutrams=$(grep -c "lut_custom" ZUMA_custom_generated.v)
    eluts=$(grep -c "elut_custom" ZUMA_custom_generated.v)
    muxluts=$((lutrams - eluts))

    echo
    echo "Overlay uses $eluts embedded LUTs and $muxluts routing/MUX LUTs, so $lutrams LUTRAMs in total."
}
