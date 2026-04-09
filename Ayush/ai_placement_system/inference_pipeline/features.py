import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from .parsers import Instance, MacroPhysicalInfo


@dataclass
class GraphFeatures:
    node_names: List[str]
    node_features: np.ndarray
    edge_index: np.ndarray
    edge_weight: np.ndarray


def _safe_norm(values: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    std = np.where(std < 1e-9, 1.0, std)
    return (values - mean) / std


def build_circuitnet_like_features(
    macro_instances: Dict[str, Instance],
    lef_macros: Dict[str, MacroPhysicalInfo],
    degree: Dict[str, int],
    edges: Dict[Tuple[str, str], int],
    normalization_json: Path | None,
) -> GraphFeatures:
    names = sorted(macro_instances.keys())
    idx = {n: i for i, n in enumerate(names)}

    node_rows: List[List[float]] = []
    for name in names:
        inst = macro_instances[name]
        macro = lef_macros[inst.cell_type]

        area = macro.area
        width = macro.width
        height = macro.height
        pin_count = float(macro.pin_count)
        deg = float(degree.get(name, 0))

        conn_strength = 0.0
        for (u, v), w in edges.items():
            if u == name or v == name:
                conn_strength += float(w)

        aspect_ratio = width / max(height, 1e-9)

        node_rows.append([
            area,
            width,
            height,
            pin_count,
            deg,
            conn_strength,
            aspect_ratio,
        ])

    node_features = np.asarray(node_rows, dtype=np.float32)

    if normalization_json and normalization_json.exists():
        data = json.loads(normalization_json.read_text(encoding="utf-8"))
        mean = np.asarray(data.get("node_mean", [0.0] * node_features.shape[1]), dtype=np.float32)
        std = np.asarray(data.get("node_std", [1.0] * node_features.shape[1]), dtype=np.float32)
        if mean.shape[0] == node_features.shape[1] and std.shape[0] == node_features.shape[1]:
            node_features = _safe_norm(node_features, mean, std)

    src: List[int] = []
    dst: List[int] = []
    wts: List[float] = []

    for (u, v), w in edges.items():
        if u not in idx or v not in idx:
            continue
        ui = idx[u]
        vi = idx[v]
        src.extend([ui, vi])
        dst.extend([vi, ui])
        wts.extend([float(w), float(w)])

    # Self loops stabilize message passing for isolated nodes.
    for i in range(len(names)):
        src.append(i)
        dst.append(i)
        wts.append(1.0)

    edge_index = np.asarray([src, dst], dtype=np.int64)
    edge_weight = np.asarray(wts, dtype=np.float32)

    return GraphFeatures(
        node_names=names,
        node_features=node_features,
        edge_index=edge_index,
        edge_weight=edge_weight,
    )
