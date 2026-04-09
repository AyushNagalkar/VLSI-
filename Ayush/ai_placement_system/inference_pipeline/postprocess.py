from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .parsers import Instance, MacroPhysicalInfo


@dataclass
class MacroBox:
    x: float
    y: float
    width: float
    height: float

    @property
    def x2(self) -> float:
        return self.x + self.width

    @property
    def y2(self) -> float:
        return self.y + self.height


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(v, hi))


def _snap(value: float, grid: float) -> float:
    if grid <= 0:
        return value
    return round(value / grid) * grid


def _intersects(a: MacroBox, b: MacroBox, spacing: float) -> bool:
    return not (
        a.x2 + spacing <= b.x or b.x2 + spacing <= a.x or a.y2 + spacing <= b.y or b.y2 + spacing <= a.y
    )


def _shift_until_clear(
    box: MacroBox,
    placed: Dict[str, MacroBox],
    die_width: float,
    die_height: float,
    spacing: float,
    grid: float,
) -> MacroBox:
    max_iters = 600
    step = max(grid, spacing, 1.0)

    for _ in range(max_iters):
        collides = False
        for other in placed.values():
            if _intersects(box, other, spacing):
                collides = True
                break
        if not collides:
            return box

        # Sweep right then wrap to next row.
        nx = box.x + step
        ny = box.y
        if nx + box.width > die_width:
            nx = 0.0
            ny = box.y + step
        if ny + box.height > die_height:
            # Last resort: pin to nearest legal boundary.
            nx = _clamp(nx, 0.0, max(die_width - box.width, 0.0))
            ny = _clamp(ny, 0.0, max(die_height - box.height, 0.0))

        box = MacroBox(
            x=_snap(nx, grid),
            y=_snap(ny, grid),
            width=box.width,
            height=box.height,
        )

    return box


def postprocess_macro_placements(
    xy_by_instance: Dict[str, Tuple[float, float]],
    macro_instances: Dict[str, Instance],
    lef_macros: Dict[str, MacroPhysicalInfo],
    die_width: float,
    die_height: float,
    placement_grid: float,
    min_spacing: float,
) -> Dict[str, MacroBox]:
    # Place larger blocks first to reduce hard overlap cascades.
    order = sorted(
        xy_by_instance.keys(),
        key=lambda n: lef_macros[macro_instances[n].cell_type].area,
        reverse=True,
    )

    placed: Dict[str, MacroBox] = {}

    for name in order:
        inst = macro_instances[name]
        macro = lef_macros[inst.cell_type]
        px, py = xy_by_instance[name]

        x = _snap(px, placement_grid)
        y = _snap(py, placement_grid)

        x = _clamp(x, 0.0, max(die_width - macro.width, 0.0))
        y = _clamp(y, 0.0, max(die_height - macro.height, 0.0))

        box = MacroBox(x=x, y=y, width=macro.width, height=macro.height)
        box = _shift_until_clear(
            box=box,
            placed=placed,
            die_width=die_width,
            die_height=die_height,
            spacing=min_spacing,
            grid=placement_grid,
        )

        box = MacroBox(
            x=_clamp(box.x, 0.0, max(die_width - box.width, 0.0)),
            y=_clamp(box.y, 0.0, max(die_height - box.height, 0.0)),
            width=box.width,
            height=box.height,
        )
        placed[name] = box

    return placed
