"""Spec extraction and matching against the target CPU / RAM / GPU baseline.

Baseline requested by the user:
  - CPU: Intel Core i5-8400  OR  AMD Ryzen 5 2600   (or better)
  - RAM: 12 GB or more
  - GPU: NVIDIA GeForce GTX 1660  OR  AMD Radeon RX 5500 XT  (or better)

CPU/GPU "or better" is approximated with a hand-curated relative performance
score. Both baseline chips are pinned to score 100; anything scored >= 100
is treated as meeting the bar. The tables are intentionally limited to
chips plausible in a sub-$540 prebuilt desktop and can be extended.
"""
import re
from dataclasses import dataclass, field
from typing import Optional

# Higher score = faster. Keys are normalized (lowercase, spaces collapsed).
CPU_SCORES = {
    # Intel Core i3 (below baseline)
    "i3-8100": 70, "i3-9100": 74, "i3-10100": 80, "i3-10105": 81, "i3-12100": 92,
    # Intel Core i5 (baseline: i5-8400 = 100)
    "i5-7400": 90, "i5-8400": 100, "i5-8500": 103, "i5-8600": 108,
    "i5-9400": 105, "i5-9400f": 105, "i5-9500": 108, "i5-9600": 112, "i5-9600k": 115,
    "i5-10400": 112, "i5-10400f": 112, "i5-10500": 115, "i5-10600": 118, "i5-10600k": 122,
    "i5-11400": 120, "i5-11400f": 120, "i5-11600": 123, "i5-11600k": 128,
    "i5-12400": 130, "i5-12400f": 130, "i5-12500": 133, "i5-12600": 136, "i5-12600k": 145,
    "i5-13400": 138, "i5-13400f": 138, "i5-13600k": 150,
    # Intel Core i7 / i9 (all comfortably above baseline)
    "i7-8700": 130, "i7-9700": 138, "i7-9700f": 138, "i7-10700": 145, "i7-10700f": 145,
    "i7-11700": 150, "i7-12700": 165, "i7-12700f": 165, "i7-13700": 175,
    "i9-9900": 150, "i9-10900": 160, "i9-11900": 165, "i9-12900": 180, "i9-13900": 195,
    # AMD Ryzen 3 (below baseline)
    "ryzen 3 1200": 60, "ryzen 3 2200g": 65, "ryzen 3 3100": 85, "ryzen 3 3300x": 92,
    "ryzen 3 4100": 88,
    # AMD Ryzen 5 (baseline: ryzen 5 2600 = 100)
    "ryzen 5 1600": 92, "ryzen 5 1600af": 95, "ryzen 5 2600": 100, "ryzen 5 2600x": 104,
    "ryzen 5 3500": 105, "ryzen 5 3500x": 107, "ryzen 5 3600": 112, "ryzen 5 3600x": 115,
    "ryzen 5 3600xt": 117, "ryzen 5 4500": 116, "ryzen 5 4600g": 118,
    "ryzen 5 5500": 122, "ryzen 5 5600": 128, "ryzen 5 5600g": 124, "ryzen 5 5600x": 130,
    "ryzen 5 7600": 145, "ryzen 5 7600x": 150,
    # AMD Ryzen 7 / 9 (all comfortably above baseline)
    "ryzen 7 1700": 105, "ryzen 7 2700": 118, "ryzen 7 2700x": 122, "ryzen 7 3700x": 135,
    "ryzen 7 3800x": 138, "ryzen 7 5700g": 132, "ryzen 7 5700x": 148, "ryzen 7 5800x": 152,
    "ryzen 7 7700": 165, "ryzen 7 7700x": 172,
    "ryzen 9 3900x": 165, "ryzen 9 5900x": 178, "ryzen 9 5950x": 190, "ryzen 9 7900x": 200,
}

GPU_SCORES = {
    # Below baseline
    "gtx 1050": 45, "gtx 1050 ti": 52, "gtx 1060": 68, "gtx 1650": 72, "gtx 1650 super": 82,
    "rx 570": 65, "rx 580": 70, "rx 5300": 62, "rx 6400": 68,
    # Baseline: gtx 1660 = 100, rx 5500 xt = 100
    "gtx 1660": 100, "gtx 1660 super": 108, "gtx 1660 ti": 110,
    "rx 5500 xt": 100, "rx 6500 xt": 98,
    # Above baseline
    "rtx 2060": 118, "rtx 2060 super": 125, "rtx 2070": 128, "rtx 2070 super": 135,
    "rtx 2080": 140, "rtx 2080 super": 145, "rtx 2080 ti": 160,
    "rtx 3050": 115, "rtx 3060": 135, "rtx 3060 ti": 148, "rtx 3070": 165, "rtx 3070 ti": 172,
    "rtx 3080": 190, "rtx 3080 ti": 200, "rtx 3090": 210,
    "rtx 4060": 150, "rtx 4060 ti": 165, "rtx 4070": 185, "rtx 4070 ti": 200, "rtx 4080": 230,
    "rx 5600 xt": 108, "rx 5700": 118, "rx 5700 xt": 130,
    "rx 6600": 120, "rx 6600 xt": 130, "rx 6650 xt": 133, "rx 6700": 140, "rx 6700 xt": 150,
    "rx 6750 xt": 155, "rx 6800": 165, "rx 6800 xt": 178, "rx 6900 xt": 190,
    "rx 7600": 140, "rx 7700 xt": 165, "rx 7800 xt": 178,
}


def _normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("™", "").replace("®", "")
    text = re.sub(r"[‐-―]", "-", text)  # unicode dashes -> hyphen
    text = re.sub(r"\s+", " ", text)
    return text


def _best_match(normalized_text: str, table: dict) -> Optional[tuple]:
    """Return (matched_key, score) for the highest-scoring key found in text."""
    best = None
    for key, score in table.items():
        pattern = re.escape(key).replace(r"\ ", r"[\s-]*")
        if re.search(rf"(?<![a-z0-9]){pattern}(?![a-z0-9])", normalized_text):
            if best is None or score > best[1]:
                best = (key, score)
    return best


def extract_cpu(text: str) -> Optional[tuple]:
    return _best_match(_normalize(text), CPU_SCORES)


def extract_gpu(text: str) -> Optional[tuple]:
    return _best_match(_normalize(text), GPU_SCORES)


_RAM_PATTERNS = [
    re.compile(r"(\d{1,3})\s*gb\s*(?:ddr\d[a-z]?)?\s*ram\b", re.I),
    re.compile(r"\bram[:\s]*(\d{1,3})\s*gb\b", re.I),
    re.compile(r"\bmemory[:\s]*(\d{1,3})\s*gb\b", re.I),
    re.compile(r"(\d{1,3})\s*gb\s*(?:ddr\d[a-z]?)?\s*memory\b", re.I),
]


def extract_ram_gb(text: str) -> Optional[int]:
    """Best-effort extraction of RAM size in GB, distinct from storage GB."""
    normalized = _normalize(text)
    candidates = []
    for pattern in _RAM_PATTERNS:
        for m in pattern.finditer(normalized):
            candidates.append(int(m.group(1)))
    if not candidates:
        return None
    return max(candidates)


@dataclass
class SpecMatch:
    meets_cpu: bool
    meets_ram: bool
    meets_gpu: bool
    cpu_found: Optional[str] = None
    ram_found: Optional[int] = None
    gpu_found: Optional[str] = None
    reasons: list = field(default_factory=list)

    @property
    def meets_all(self) -> bool:
        return self.meets_cpu and self.meets_ram and self.meets_gpu


def evaluate_specs(text: str, min_cpu_score: int = 100, min_ram_gb: int = 12,
                    min_gpu_score: int = 100) -> SpecMatch:
    reasons = []

    cpu_match = extract_cpu(text)
    meets_cpu = bool(cpu_match and cpu_match[1] >= min_cpu_score)
    if not cpu_match:
        reasons.append("CPU model not detected in listing text")
    elif not meets_cpu:
        reasons.append(f"CPU '{cpu_match[0]}' is below the required tier")

    ram_gb = extract_ram_gb(text)
    meets_ram = bool(ram_gb is not None and ram_gb >= min_ram_gb)
    if ram_gb is None:
        reasons.append("RAM size not detected in listing text")
    elif not meets_ram:
        reasons.append(f"RAM {ram_gb}GB is below the required {min_ram_gb}GB")

    gpu_match = extract_gpu(text)
    meets_gpu = bool(gpu_match and gpu_match[1] >= min_gpu_score)
    if not gpu_match:
        reasons.append("GPU model not detected in listing text")
    elif not meets_gpu:
        reasons.append(f"GPU '{gpu_match[0]}' is below the required tier")

    return SpecMatch(
        meets_cpu=meets_cpu,
        meets_ram=meets_ram,
        meets_gpu=meets_gpu,
        cpu_found=cpu_match[0] if cpu_match else None,
        ram_found=ram_gb,
        gpu_found=gpu_match[0] if gpu_match else None,
        reasons=reasons,
    )
