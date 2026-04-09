from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Any

from .features import build_circuitnet_like_features
from .inference import GNNInferenceEngine
from .parsers import Instance, build_macro_connectivity, parse_lef, parse_verilog
from .postprocess import postprocess_macro_placements
from .tcl_writer import write_innovus_tcl


@dataclass
class PipelineConfig:
    verilog: Path
    lef: Path
    out_tcl: Path
    out_json: Path
    model_path: Path | None
    normalization_json: Path | None
    die_width: float
    die_height: float
    core_margin: float
    placement_grid: float
    min_spacing: float
    macro_area_threshold: float
    assume_model_output_normalized: bool
    allow_synthetic_top_macro: bool
    emit_macro_tcl_only_when_gnn: bool
    device: str


def run_pipeline(cfg: PipelineConfig) -> Dict[str, Any]:
    netlist = parse_verilog(cfg.verilog)
    lef_macros = parse_lef(cfg.lef)

    macro_instances, degree, edges = build_macro_connectivity(
        netlist=netlist,
        lef_macros=lef_macros,
        macro_area_threshold=cfg.macro_area_threshold,
    )

    if not macro_instances:
        # Fallback for block-level LEF + flat standard-cell netlist: treat top module as one macro.
        if cfg.allow_synthetic_top_macro and netlist.top_module in lef_macros:
            synthetic_name = f"{netlist.top_module}_TOP_MACRO"
            macro_instances = {
                synthetic_name: Instance(
                    name=synthetic_name,
                    cell_type=netlist.top_module,
                    connections={},
                )
            }
            degree = {synthetic_name: 0}
            edges = {}
        else:
            raise ValueError(
                "No macro instances found. Check LEF classes/area threshold or Verilog cell names."
            )

    graph_features = build_circuitnet_like_features(
        macro_instances=macro_instances,
        lef_macros=lef_macros,
        degree=degree,
        edges=edges,
        normalization_json=cfg.normalization_json,
    )

    engine = GNNInferenceEngine(model_path=cfg.model_path, device=cfg.device)
    pred = engine.predict(
        gf=graph_features,
        macro_instances=macro_instances,
        lef_macros=lef_macros,
        die_width=cfg.die_width,
        die_height=cfg.die_height,
        assume_model_output_normalized=cfg.assume_model_output_normalized,
    )

    placed = postprocess_macro_placements(
        xy_by_instance=pred.xy_by_instance,
        macro_instances=macro_instances,
        lef_macros=lef_macros,
        die_width=cfg.die_width,
        die_height=cfg.die_height,
        placement_grid=cfg.placement_grid,
        min_spacing=cfg.min_spacing,
    )

    placements_for_tcl = placed
    if cfg.emit_macro_tcl_only_when_gnn and not pred.used_gnn_model:
        placements_for_tcl = {}

    cfg.out_tcl.parent.mkdir(parents=True, exist_ok=True)
    cfg.out_json.parent.mkdir(parents=True, exist_ok=True)

    write_innovus_tcl(
        out_tcl=cfg.out_tcl,
        verilog_path=cfg.verilog,
        lef_path=cfg.lef,
        top_module=netlist.top_module,
        die_width=cfg.die_width,
        die_height=cfg.die_height,
        core_margin=cfg.core_margin,
        placements=placements_for_tcl,
    )

    json_payload = {
        "config": {
            k: str(v) if isinstance(v, Path) else v
            for k, v in asdict(cfg).items()
        },
        "summary": {
            "top_module": netlist.top_module,
            "num_instances": len(netlist.instances),
            "num_macros": len(macro_instances),
            "num_edges": int(graph_features.edge_index.shape[1]),
            "placement_source": pred.placement_source,
            "gnn_placement_used": pred.used_gnn_model,
            "macros_emitted_to_tcl": len(placements_for_tcl),
        },
        "placements": {
            name: {
                "x": box.x,
                "y": box.y,
                "width": box.width,
                "height": box.height,
                "x2": box.x2,
                "y2": box.y2,
            }
            for name, box in sorted(placed.items())
        },
    }
    cfg.out_json.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")

    return json_payload
