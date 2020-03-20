#!/bin/bash

#uses a clock file see: http://code.google.com/p/vtr-verilog-to-routing/wiki/ClocksFile
if [ ! -f user_clocks.clock ]; then
       echo "# [bench_name] [top-level clk name]" > user_clocks.clock
       echo "abc_out				clock" >> user_clocks.clock
fi


cp user_clocks.clock  $VTR_DIR/vtr_flow/misc/user_clocks.clock

  # --echo_file on ## echo_file is for VPR 7 only
  #$VTR_DIR/vpr/vpr ARCH_vpr7.xml zuma --net_file netlist.net --place_file place.p --route_file route.r --blif_file clock_fixed.blif --timing_analysis off --route_chan_width ZUMA_CHAN_W --fix_pins iopads.p
$VTR_DIR/vpr/vpr ARCH_vpr8_timing.xml zuma \
--net_file netlist.net \
--place_file place.p \
--route_file route.r \
--circuit_file abc_out.blif \
--timing_analysis on \
--full_stats on \
--timing_report_detail debug \
--disp off \
--route_chan_width ZUMA_CHAN_W \
--echo_file on \
--read_rr_graph rr_graph_timing.xml
