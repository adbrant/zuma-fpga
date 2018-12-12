#uses a clock file see: http://code.google.com/p/vtr-verilog-to-routing/wiki/ClocksFile
if [ ! -f user_clocks.clock ]; then
        echo "# [bench_name] [top-level clk name]" > user_clocks.clock
        echo "abc_out				clock" >> user_clocks.clock
fi

#is vpr 7 unset?
if [ "$USE_VPR_7" -eq 0 ]; then
    $VTR_DIR/vtr_flow/scripts/hack_fix_lines_and_latches.pl ./abc_out.blif clock_fixed.blif user_clocks.clock || cp ./abc_out.blif clock_fixed.blif
#vpr 7 is set so copy the clock file
else
    cp user_clocks.clock  $VTR_DIR/vtr_flow/misc/user_clocks.clock
fi
#is vpr 7 unset?
if [ "$USE_VPR_7" -eq 0 ]; then
    $VTR_DIR/vpr/vpr ARCH.xml zuma \
    --net_file netlist.net \
    --place_file place.p \
    --route_file route.r \
    --blif_file clock_fixed.blif \
    --timing_analysis off \
    --nodisp \
    --route_chan_width ZUMA_CHAN_W
else
    # --echo_file on ## echo_file is for VPR 7 only
    #$VTR_DIR/vpr/vpr ARCH_vpr7.xml zuma --net_file netlist.net --place_file place.p --route_file route.r --blif_file clock_fixed.blif --timing_analysis off --route_chan_width ZUMA_CHAN_W --fix_pins iopads.p
    $VTR_DIR/vpr/vpr ARCH_vpr7.xml zuma \
    --net_file netlist.net \
    --place_file place.p \
    --route_file route.r \
    --blif_file abc_out.blif \
    --timing_analysis off \
    --nodisp \
    --route_chan_width ZUMA_CHAN_W \
    --echo_file on
fi
