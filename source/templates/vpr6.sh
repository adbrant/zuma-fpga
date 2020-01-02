#!/usr/bin/bash

#uses a clock file see: http://code.google.com/p/vtr-verilog-to-routing/wiki/ClocksFile
if [ ! -f user_clocks.clock ]; then
        echo "# [bench_name] [top-level clk name]" > user_clocks.clock
        echo "abc_out				clock" >> user_clocks.clock
fi

$VTR_DIR/vtr_flow/scripts/hack_fix_lines_and_latches.pl ./abc_out.blif clock_fixed.blif user_clocks.clock || cp ./abc_out.blif clock_fixed.blif

$VTR_DIR/vpr/vpr ARCH_vpr6.xml zuma \
    --net_file netlist.net \
    --place_file place.p \
    --route_file route.r \
    --blif_file clock_fixed.blif \
    --timing_analysis off \
    --nodisp \
    --route_chan_width ZUMA_CHAN_W
