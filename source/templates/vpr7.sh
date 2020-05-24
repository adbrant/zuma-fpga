#!/usr/bin/env bash

#uses a clock file see: http://code.google.com/p/vtr-verilog-to-routing/wiki/ClocksFile
if [ ! -f user_clocks.clock ]; then
        echo "# [bench_name] [top-level clk name]" > user_clocks.clock
        echo "abc_out				clock" >> user_clocks.clock
fi

cp user_clocks.clock  $VTR_DIR/vtr_flow/misc/user_clocks.clock

$VTR_DIR/vpr/vpr ARCH_vpr7.xml zuma \
    --net_file netlist.net \
    --place_file place.p \
    --route_file route.r \
    --blif_file abc_out.blif \
    --timing_analysis off \
    --nodisp \
    --route_chan_width ZUMA_CHAN_W \
    --echo_file on
