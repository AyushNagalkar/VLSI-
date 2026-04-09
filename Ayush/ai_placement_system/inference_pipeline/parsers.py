import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class MacroPhysicalInfo:
    name: str
    width: float
    height: float
    pin_count: int
    macro_class: str = ""

    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass
class Instance:
    name: str
    cell_type: str
    connections: Dict[str, str]


@dataclass
class NetlistData:
    top_module: str
    instances: Dict[str, Instance] = field(default_factory=dict)
    net_to_instances: Dict[str, List[str]] = field(default_factory=dict)


def _strip_verilog_comments(verilog_text: str) -> str:
    no_block = re.sub(r"/\*.*?\*/", "", verilog_text, flags=re.S)
    no_line = re.sub(r"//.*", "", no_block)
    return no_line


def parse_verilog(verilog_path: Path) -> NetlistData:
    text = verilog_path.read_text(encoding="utf-8", errors="ignore")
    text = _strip_verilog_comments(text)

    module_match = re.search(r"\bmodule\s+(\w+)\b", text)
    top_module = module_match.group(1) if module_match else "top"

    statements = [s.strip() for s in text.split(";") if s.strip()]

    # Matches: cell_type inst_name ( .PIN(net), ... )
    # Handles escaped instance names like: \inst_name[3]
    inst_pattern = re.compile(
        r"^(?!module\b|endmodule\b|wire\b|input\b|output\b|inout\b|assign\b|parameter\b)([A-Za-z_$][\w$]*)\s+(\\?[^\s(]+)\s*\((.*)\)$",
        flags=re.S,
    )
    conn_pattern = re.compile(r"\.([A-Za-z_]\w*)\s*\(\s*([^\)]+)\s*\)")

    instances: Dict[str, Instance] = {}
    net_to_instances: Dict[str, List[str]] = {}

    for stmt in statements:
        m = inst_pattern.match(stmt)
        if not m:
            continue

        cell_type, inst_name, conn_body = m.groups()
        pin_map: Dict[str, str] = {}

        for pin, net_expr in conn_pattern.findall(conn_body):
            net = net_expr.strip()
            # Ignore constants and bus concatenations during graph construction.
            if re.match(r"^\d+'[bhdBHD][0-9a-fA-FxXzZ_]+$", net) or "{" in net:
                continue
            pin_map[pin] = net
            net_to_instances.setdefault(net, []).append(inst_name)

        instances[inst_name] = Instance(
            name=inst_name,
            cell_type=cell_type,
            connections=pin_map,
        )

    return NetlistData(top_module=top_module, instances=instances, net_to_instances=net_to_instances)


def parse_lef(lef_path: Path) -> Dict[str, MacroPhysicalInfo]:
    lines = lef_path.read_text(encoding="utf-8", errors="ignore").splitlines()

    macros: Dict[str, MacroPhysicalInfo] = {}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line.startswith("MACRO "):
            i += 1
            continue

        macro_name = line.split()[1]
        width = 0.0
        height = 0.0
        pin_count = 0
        macro_class = ""

        i += 1
        while i < len(lines):
            inner = lines[i].strip()
            if inner.startswith("CLASS "):
                parts = inner.split()
                macro_class = parts[1] if len(parts) > 1 else ""
            elif inner.startswith("SIZE "):
                # LEF format: SIZE <w> BY <h> ;
                m = re.search(r"SIZE\s+([0-9eE+\-.]+)\s+BY\s+([0-9eE+\-.]+)", inner)
                if m:
                    width = float(m.group(1))
                    height = float(m.group(2))
            elif inner.startswith("PIN "):
                pin_count += 1
            elif inner.startswith(f"END {macro_name}"):
                break
            i += 1

        macros[macro_name] = MacroPhysicalInfo(
            name=macro_name,
            width=width,
            height=height,
            pin_count=pin_count,
            macro_class=macro_class,
        )
        i += 1

    return macros


def build_macro_connectivity(
    netlist: NetlistData,
    lef_macros: Dict[str, MacroPhysicalInfo],
    macro_area_threshold: float,
) -> Tuple[Dict[str, Instance], Dict[str, int], Dict[Tuple[str, str], int]]:
    # Keep only macro-like instances used in netlist.
    macro_instances: Dict[str, Instance] = {}
    for inst_name, inst in netlist.instances.items():
        macro_def = lef_macros.get(inst.cell_type)
        if not macro_def:
            continue
        is_block_class = macro_def.macro_class.upper() in {"BLOCK", "RING", "COVER"}
        is_large = macro_def.area >= macro_area_threshold
        if is_block_class or is_large:
            macro_instances[inst_name] = inst

    degree: Dict[str, int] = {name: 0 for name in macro_instances}
    edges: Dict[Tuple[str, str], int] = {}

    for _, connected in netlist.net_to_instances.items():
        macro_connected = [n for n in connected if n in macro_instances]
        unique = list(dict.fromkeys(macro_connected))
        if len(unique) < 2:
            continue
        for inst in unique:
            degree[inst] += len(unique) - 1
        for i in range(len(unique)):
            for j in range(i + 1, len(unique)):
                u = unique[i]
                v = unique[j]
                key = (u, v) if u < v else (v, u)
                edges[key] = edges.get(key, 0) + 1

    return macro_instances, degree, edges
