#!/usr/bin/env bash

  # --echo_file on ## echo_file is for VPR 7 only
  #$VTR_DIR/vpr/vpr ARCH_vpr7.xml zuma --net_file netlist.net --place_file place.p --route_file route.r --blif_file clock_fixed.blif --timing_analysis off --route_chan_width ZUMA_CHAN_W --fix_pins iopads.p
$VTR_DIR/build/vpr/vpr ARCH_vpr8_timing.xml zuma \
--net_file netlist.net \
--place_file place.p \
--route_file route.r \
--circuit_file clock_fixed.blif \
--timing_analysis on \
--full_stats on \
--timing_report_detail debug \
--routing_budgets_algorithm minimax \
--timing_report_skew on \
--post_place_timing_report postplacetiming \
--save_routing_per_iteration on \
--disp off \
--route_chan_width ZUMA_CHAN_W \
--echo_file on \
--read_rr_graph rr_graph_timing.xml
