from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict

from .postprocess import MacroBox


def write_innovus_tcl(
    out_tcl: Path,
    verilog_path: Path,
    lef_path: Path,
    top_module: str,
    die_width: float,
    die_height: float,
    core_margin: float,
    placements: Dict[str, MacroBox],
    orient: str = "N",
) -> None:
    core_llx = core_margin
    core_lly = core_margin
    core_urx = max(core_margin, die_width - core_margin)
    core_ury = max(core_margin, die_height - core_margin)

    lines = []
    lines.append("# Auto-generated Innovus TCL for full floorplanning + fixed macro placement")
    lines.append(f"# Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("# -----------------------------")
    lines.append("# User-tunable floorplan knobs")
    lines.append("# -----------------------------")
    lines.append("set PWR_NET VDD")
    lines.append("set GND_NET VSS")
    lines.append("set RING_H_LAYER M7")
    lines.append("set RING_V_LAYER M8")
    lines.append("set STRIPE_LAYER M6")
    lines.append("set RING_WIDTH 2.0")
    lines.append("set RING_SPACING 1.0")
    lines.append("set RING_OFFSET 2.0")
    lines.append("set STRIPE_WIDTH 1.2")
    lines.append("set STRIPE_SPACING 1.2")
    lines.append("set STRIPE_PITCH 40.0")
    lines.append("set MACRO_HALO 4.0")
    lines.append("set MACRO_CHANNEL 6.0")
    lines.append("")

    lines.append("proc maybe {cmd} {")
    lines.append("  if {[catch {uplevel 1 $cmd} err]} {")
    lines.append("    puts \"INFO: command skipped -> $cmd\"")
    lines.append("    puts \"INFO: reason -> $err\"")
    lines.append("  }")
    lines.append("}")
    lines.append("")

    lines.append("# -----------------------------")
    lines.append("# Phase A: Design initialization")
    lines.append("# -----------------------------")
    lines.append("set init_design_settop 1")
    lines.append(f"set init_verilog \"{verilog_path.as_posix()}\"")
    lines.append(f"set init_lef_file \"{lef_path.as_posix()}\"")
    lines.append(f"set init_top_cell \"{top_module}\"")
    lines.append("init_design")
    lines.append("")

    lines.append("# Pick a valid site from loaded tech LEF; fallback to 'core'.")
    lines.append("set fp_site [lindex [dbGet head.sites.name] 0]")
    lines.append("if {$fp_site eq \"\"} { set fp_site core }")
    lines.append("")

    lines.append("# -----------------------------")
    lines.append("# Phase B: Floorplan creation")
    lines.append("# -----------------------------")
    lines.append(
        f"floorPlan -site $fp_site -d {die_width:.3f} {die_height:.3f} {core_llx:.3f} {core_lly:.3f} {die_width-core_urx:.3f} {die_height-core_ury:.3f}"
    )
    lines.append("maybe {checkFPlan}")
    lines.append("maybe {setDesignMode -process 28}")
    lines.append("maybe {setPlaceMode -place_global_uniform_density true}")
    lines.append("")

    lines.append("# Connect global PG nets if corresponding pins exist in the library.")
    lines.append("maybe {clearGlobalNets}")
    lines.append("maybe {globalNetConnect $PWR_NET -type pgpin -pin $PWR_NET -inst *}")
    lines.append("maybe {globalNetConnect $GND_NET -type pgpin -pin $GND_NET -inst *}")
    lines.append("maybe {globalNetConnect $PWR_NET -type tiehi -inst *}")
    lines.append("maybe {globalNetConnect $GND_NET -type tielo -inst *}")
    lines.append("")

    lines.append("# -----------------------------")
    lines.append("# Phase C: Power plan (rings/stripes)")
    lines.append("# -----------------------------")
    lines.append("maybe {setAddRingMode -stacked_via_top_layer $RING_V_LAYER -stacked_via_bottom_layer M1}")
    lines.append(
        "maybe {addRing -nets [list $PWR_NET $GND_NET] -type core_rings -layer [list top $RING_H_LAYER bottom $RING_H_LAYER left $RING_V_LAYER right $RING_V_LAYER] -width [list $RING_WIDTH $RING_WIDTH $RING_WIDTH $RING_WIDTH] -spacing [list $RING_SPACING $RING_SPACING $RING_SPACING $RING_SPACING] -offset [list $RING_OFFSET $RING_OFFSET $RING_OFFSET $RING_OFFSET]}"
    )
    lines.append(
        "maybe {addStripe -nets [list $PWR_NET $GND_NET] -layer $STRIPE_LAYER -direction vertical -width $STRIPE_WIDTH -spacing $STRIPE_SPACING -set_to_set_distance $STRIPE_PITCH}"
    )
    lines.append("maybe {sroute -connect {corePin} -nets [list $PWR_NET $GND_NET]}")
    lines.append("")

    lines.append("# -----------------------------")
    lines.append("# Phase D: Macro placement")
    lines.append("# -----------------------------")
    if placements:
        lines.append("setPlaceMode -modulePlan true")
        lines.append("# Macro placement from GNN predictions (post-processed)")
        for name in sorted(placements.keys()):
            b = placements[name]
            lines.append(f"placeInstance {name} {b.x:.3f} {b.y:.3f} {orient}")
            lines.append(f"setInstancePlacementStatus {name} fixed")
            lines.append(f"maybe {{addHaloToBlock $MACRO_HALO $MACRO_HALO $MACRO_HALO $MACRO_HALO {name}}}")

            blk_llx = max(0.0, b.x - 1.0)
            blk_lly = max(0.0, b.y - 1.0)
            blk_urx = b.x2 + 1.0
            blk_ury = b.y2 + 1.0
            lines.append(
                f"maybe {{createPlaceBlockage -type hard -name PB_{name} -box {{{blk_llx:.3f} {blk_lly:.3f} {blk_urx:.3f} {blk_ury:.3f}}}}}"
            )

        lines.append("")
        lines.append("# Reserve channels around macros and lock all macro instances.")
        lines.append("maybe {setPlaceMode -place_global_blockage_in_channel true}")
        lines.append("maybe {setPlaceMode -place_global_channel_width $MACRO_CHANNEL}")
        lines.append("foreach inst [get_db insts .name] {")
        lines.append("  if {[dbGet [dbGetInstByName $inst].baseClass] == \"block\"} {")
        lines.append("    setInstancePlacementStatus $inst fixed")
        lines.append("  }")
        lines.append("}")
        lines.append("")
    else:
        lines.append("puts \"INFO: No GNN macro placements emitted. Innovus will decide macro placement.\"")
        lines.append("")

    lines.append("# -----------------------------")
    lines.append("# Phase E: Placement, CTS, Routing")
    lines.append("# -----------------------------")
    lines.append("maybe {place_opt_design}")
    lines.append("maybe {optDesign -preCTS}")
    lines.append("maybe {clockDesign}")
    lines.append("maybe {ccopt_design}")
    lines.append("maybe {optDesign -postCTS}")
    lines.append("maybe {routeDesign}")
    lines.append("maybe {optDesign -postRoute}")
    lines.append("")
    lines.append("# -----------------------------")
    lines.append("# Phase F: Validation + checkpoints")
    lines.append("# -----------------------------")
    lines.append("maybe {checkPlace}")
    lines.append("maybe {checkRoute}")
    lines.append("maybe {verifyConnectivity -type all}")
    lines.append("maybe {verify_drc}")
    lines.append("maybe {reportCongestion -overflow}")
    lines.append("maybe {timeDesign -preCTS -expandedViews -reportOnly}")
    lines.append("maybe {timeDesign -postCTS -expandedViews -reportOnly}")
    lines.append("maybe {timeDesign -postRoute -expandedViews -reportOnly}")
    lines.append("saveDesign floorplan_macro_fixed.enc")
    lines.append("maybe {saveNetlist floorplan_macro_fixed.v}")
    lines.append("maybe {writeFPlanScript -file floorplan_macro_fixed.tcl}")
    lines.append("puts \"Full backend TCL completed.\"")

    out_tcl.write_text("\n".join(lines) + "\n", encoding="utf-8")
