from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import torch

from .features import GraphFeatures
from .parsers import Instance, MacroPhysicalInfo


@dataclass
class PlacementPrediction:
    xy_by_instance: Dict[str, Tuple[float, float]]
    used_gnn_model: bool
    placement_source: str


class GNNInferenceEngine:
    def __init__(self, model_path: Path | None, device: str = "cpu"):
        self.device = torch.device(device)
        self.model = None
        self.model_path = model_path

        if model_path is None:
            return

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Support TorchScript first, then generic torch.load object.
        try:
            self.model = torch.jit.load(str(model_path), map_location=self.device)
            self.model.eval()
            return
        except Exception:
            pass

        loaded = torch.load(str(model_path), map_location=self.device)
        if isinstance(loaded, torch.nn.Module):
            self.model = loaded
            self.model.eval()
        else:
            # A state_dict alone is not enough to instantiate unknown architecture.
            self.model = None

    def _run_model(self, gf: GraphFeatures) -> np.ndarray | None:
        if self.model is None:
            return None

        x = torch.tensor(gf.node_features, dtype=torch.float32, device=self.device)
        edge_index = torch.tensor(gf.edge_index, dtype=torch.long, device=self.device)
        edge_weight = torch.tensor(gf.edge_weight, dtype=torch.float32, device=self.device)

        candidates = [
            lambda: self.model(x),
            lambda: self.model(x, edge_index),
            lambda: self.model(x, edge_index, edge_weight),
            lambda: self.model(
                {
                    "x": x,
                    "edge_index": edge_index,
                    "edge_weight": edge_weight,
                }
            ),
        ]

        for fn in candidates:
            try:
                with torch.no_grad():
                    out = fn()
                if isinstance(out, (tuple, list)):
                    out = out[0]
                out = out.detach().cpu().numpy()
                if out.ndim == 2 and out.shape[1] >= 2:
                    return out[:, :2].astype(np.float32)
            except Exception:
                continue

        return None

    def _heuristic_xy(
        self,
        gf: GraphFeatures,
        macro_instances: Dict[str, Instance],
        lef_macros: Dict[str, MacroPhysicalInfo],
        die_width: float,
        die_height: float,
    ) -> np.ndarray:
        # Stable fallback when model contract is unknown; area-sorted serpentine rows.
        sizes = []
        for name in gf.node_names:
            inst = macro_instances[name]
            m = lef_macros[inst.cell_type]
            sizes.append((name, m.width, m.height, m.area))
        sizes.sort(key=lambda t: t[3], reverse=True)

        x_cursor = 0.0
        y_cursor = 0.0
        row_h = 0.0
        direction = 1
        out: Dict[str, Tuple[float, float]] = {}

        margin = 1.0
        usable_w = max(die_width - 2 * margin, 1.0)

        for name, w, h, _ in sizes:
            if x_cursor + w > usable_w:
                y_cursor += row_h + margin
                row_h = 0.0
                direction *= -1
                x_cursor = 0.0

            x_local = x_cursor
            if direction < 0:
                x_local = max(0.0, usable_w - (x_cursor + w))

            out[name] = (x_local + margin, y_cursor + margin)
            x_cursor += w + margin
            row_h = max(row_h, h)

        ordered_xy = np.zeros((len(gf.node_names), 2), dtype=np.float32)
        for i, name in enumerate(gf.node_names):
            ordered_xy[i] = out.get(name, (0.0, 0.0))

        # Convert to normalized coordinates.
        ordered_xy[:, 0] = ordered_xy[:, 0] / max(die_width, 1e-9)
        ordered_xy[:, 1] = ordered_xy[:, 1] / max(die_height, 1e-9)
        return ordered_xy

    def predict(
        self,
        gf: GraphFeatures,
        macro_instances: Dict[str, Instance],
        lef_macros: Dict[str, MacroPhysicalInfo],
        die_width: float,
        die_height: float,
        assume_model_output_normalized: bool,
    ) -> PlacementPrediction:
        raw = self._run_model(gf)
        if raw is None:
            raw = self._heuristic_xy(gf, macro_instances, lef_macros, die_width, die_height)
            normalized = True
            used_gnn_model = False
            placement_source = "heuristic"
        else:
            normalized = assume_model_output_normalized
            used_gnn_model = True
            placement_source = "gnn_model"

        if normalized:
            raw[:, 0] = raw[:, 0] * die_width
            raw[:, 1] = raw[:, 1] * die_height

        xy_by_instance = {
            name: (float(raw[i, 0]), float(raw[i, 1]))
            for i, name in enumerate(gf.node_names)
        }

        return PlacementPrediction(
            xy_by_instance=xy_by_instance,
            used_gnn_model=used_gnn_model,
            placement_source=placement_source,
        )
