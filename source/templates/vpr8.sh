#!/usr/bin/env bash


  # --echo_file on ## echo_file is for VPR 7 only
  #$VTR_DIR/vpr/vpr ARCH_vpr7.xml zuma --net_file netlist.net --place_file place.p --route_file route.r --blif_file clock_fixed.blif --timing_analysis off --route_chan_width ZUMA_CHAN_W --fix_pins iopads.p
$VTR_DIR/vpr/vpr ARCH_vpr8.xml zuma \
--net_file netlist.net \
--place_file place.p \
--route_file route.r \
--circuit_file clock_fixed.blif \
--timing_analysis off \
--disp off \
--route_chan_width ZUMA_CHAN_W \
--echo_file on \
--write_rr_graph rr_graph.xml
