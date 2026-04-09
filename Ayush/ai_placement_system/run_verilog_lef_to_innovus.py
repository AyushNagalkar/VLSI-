"""CLI: Verilog + LEF -> fixed macro Innovus TCL using GNN predictions."""

from __future__ import annotations

import argparse
from pathlib import Path

from Ayush.ai_placement_system.inference_pipeline.pipeline import PipelineConfig, run_pipeline


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Convert Verilog + LEF to Innovus TCL with fixed macro placements",
    )
    p.add_argument("--verilog", required=True, type=Path, help="Input gate-level Verilog")
    p.add_argument("--lef", required=True, type=Path, help="Input technology/macro LEF")
    p.add_argument("--out-tcl", required=True, type=Path, help="Output Innovus TCL")
    p.add_argument("--out-json", required=True, type=Path, help="Output JSON placements")

    p.add_argument("--model", type=Path, default=None, help="Path to trained model (.pt/.pth/.jit)")
    p.add_argument(
        "--normalization-json",
        type=Path,
        default=None,
        help="Feature normalization stats JSON (node_mean/node_std)",
    )

    p.add_argument("--die-width", type=float, required=True, help="Die width in microns")
    p.add_argument("--die-height", type=float, required=True, help="Die height in microns")
    p.add_argument("--core-margin", type=float, default=10.0, help="Core margin in microns")
    p.add_argument("--placement-grid", type=float, default=1.0, help="Grid snap in microns")
    p.add_argument("--min-spacing", type=float, default=2.0, help="Minimum macro spacing in microns")
    p.add_argument(
        "--macro-area-threshold",
        type=float,
        default=1000.0,
        help="Fallback area threshold to classify macros",
    )
    p.add_argument(
        "--model-output-normalized",
        action="store_true",
        help="Set if the model outputs normalized coordinates in [0,1]",
    )
    p.add_argument(
        "--allow-synthetic-top-macro",
        action="store_true",
        help="Allow fallback placement of one synthetic top-level macro when no macro instances are found",
    )
    p.add_argument(
        "--always-emit-macro-tcl",
        action="store_true",
        help="Emit macro place/fix commands in TCL even when fallback heuristic placements were used",
    )
    p.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="Inference device")

    return p.parse_args()


def main() -> None:
    args = parse_args()

    cfg = PipelineConfig(
        verilog=args.verilog,
        lef=args.lef,
        out_tcl=args.out_tcl,
        out_json=args.out_json,
        model_path=args.model,
        normalization_json=args.normalization_json,
        die_width=args.die_width,
        die_height=args.die_height,
        core_margin=args.core_margin,
        placement_grid=args.placement_grid,
        min_spacing=args.min_spacing,
        macro_area_threshold=args.macro_area_threshold,
        assume_model_output_normalized=args.model_output_normalized,
        allow_synthetic_top_macro=args.allow_synthetic_top_macro,
        emit_macro_tcl_only_when_gnn=(not args.always_emit_macro_tcl),
        device=args.device,
    )

    result = run_pipeline(cfg)
    print("Pipeline completed.")
    print(f"Top module: {result['summary']['top_module']}")
    print(f"Instances: {result['summary']['num_instances']}")
    print(f"Macros placed: {result['summary']['num_macros']}")
    print(f"Placement source: {result['summary']['placement_source']}")
    print(f"Macros emitted to TCL: {result['summary']['macros_emitted_to_tcl']}")
    print(f"TCL output: {args.out_tcl}")
    print(f"JSON output: {args.out_json}")


if __name__ == "__main__":
    main()
