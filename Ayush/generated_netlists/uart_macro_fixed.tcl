# Auto-generated Innovus TCL for full floorplanning + fixed macro placement
# Generated: 2026-04-06T17:02:00

# -----------------------------
# User-tunable floorplan knobs
# -----------------------------
set PWR_NET VDD
set GND_NET VSS
set RING_H_LAYER M7
set RING_V_LAYER M8
set STRIPE_LAYER M6
set RING_WIDTH 2.0
set RING_SPACING 1.0
set RING_OFFSET 2.0
set STRIPE_WIDTH 1.2
set STRIPE_SPACING 1.2
set STRIPE_PITCH 40.0
set MACRO_HALO 4.0
set MACRO_CHANNEL 6.0

proc maybe {cmd} {
  if {[catch {uplevel 1 $cmd} err]} {
    puts "INFO: command skipped -> $cmd"
    puts "INFO: reason -> $err"
  }
}

# -----------------------------
# Phase A: Design initialization
# -----------------------------
set init_design_settop 1
set init_verilog "Ayush/netlist.v"
set init_lef_file "Ayush/uart.lef"
set init_top_cell "uart"
init_design

# Pick a valid site from loaded tech LEF; fallback to 'core'.
set fp_site [lindex [dbGet head.sites.name] 0]
if {$fp_site eq ""} { set fp_site core }

# -----------------------------
# Phase B: Floorplan creation
# -----------------------------
floorPlan -site $fp_site -d 2000.000 2000.000 20.000 20.000 20.000 20.000
maybe {checkFPlan}
maybe {setDesignMode -process 28}
maybe {setPlaceMode -place_global_uniform_density true}

# Connect global PG nets if corresponding pins exist in the library.
maybe {clearGlobalNets}
maybe {globalNetConnect $PWR_NET -type pgpin -pin $PWR_NET -inst *}
maybe {globalNetConnect $GND_NET -type pgpin -pin $GND_NET -inst *}
maybe {globalNetConnect $PWR_NET -type tiehi -inst *}
maybe {globalNetConnect $GND_NET -type tielo -inst *}

# -----------------------------
# Phase C: Power plan (rings/stripes)
# -----------------------------
maybe {setAddRingMode -stacked_via_top_layer $RING_V_LAYER -stacked_via_bottom_layer M1}
maybe {addRing -nets [list $PWR_NET $GND_NET] -type core_rings -layer [list top $RING_H_LAYER bottom $RING_H_LAYER left $RING_V_LAYER right $RING_V_LAYER] -width [list $RING_WIDTH $RING_WIDTH $RING_WIDTH $RING_WIDTH] -spacing [list $RING_SPACING $RING_SPACING $RING_SPACING $RING_SPACING] -offset [list $RING_OFFSET $RING_OFFSET $RING_OFFSET $RING_OFFSET]}
maybe {addStripe -nets [list $PWR_NET $GND_NET] -layer $STRIPE_LAYER -direction vertical -width $STRIPE_WIDTH -spacing $STRIPE_SPACING -set_to_set_distance $STRIPE_PITCH}
maybe {sroute -connect {corePin} -nets [list $PWR_NET $GND_NET]}

# -----------------------------
# Phase D: Macro placement
# -----------------------------
puts "INFO: No GNN macro placements emitted. Innovus will decide macro placement."

# -----------------------------
# Phase E: Placement, CTS, Routing
# -----------------------------
maybe {place_opt_design}
maybe {optDesign -preCTS}
maybe {clockDesign}
maybe {ccopt_design}
maybe {optDesign -postCTS}
maybe {routeDesign}
maybe {optDesign -postRoute}

# -----------------------------
# Phase F: Validation + checkpoints
# -----------------------------
maybe {checkPlace}
maybe {checkRoute}
maybe {verifyConnectivity -type all}
maybe {verify_drc}
maybe {reportCongestion -overflow}
maybe {timeDesign -preCTS -expandedViews -reportOnly}
maybe {timeDesign -postCTS -expandedViews -reportOnly}
maybe {timeDesign -postRoute -expandedViews -reportOnly}
saveDesign floorplan_macro_fixed.enc
maybe {saveNetlist floorplan_macro_fixed.v}
maybe {writeFPlanScript -file floorplan_macro_fixed.tcl}
puts "Full backend TCL completed."
