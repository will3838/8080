from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List
import bisect

from openpyxl import load_workbook


@dataclass(frozen=True)
class LootItem:
    item_id: str
    name: str
    weight: float
    icon_path: Path


class LootTable:
    def __init__(self, items: List[LootItem]) -> None:
        if not items:
            raise ValueError("Loot table is empty")
        self.items = items
        self.total_weight = sum(item.weight for item in items)
        self._prefix_sums: List[float] = []
        running = 0.0
        for item in items:
            running += item.weight
            self._prefix_sums.append(running)

    @classmethod
    def from_excel(cls, excel_path: Path, icons_dir: Path) -> "LootTable":
        if not excel_path.exists():
            raise FileNotFoundError(f"Missing Excel file: {excel_path}")

        workbook = load_workbook(excel_path, data_only=True)
        sheet = workbook.worksheets[0]

        items: List[LootItem] = []
        seen_ids: set[str] = set()

        for row_idx, row in enumerate(sheet.iter_rows(min_row=2, max_col=3, values_only=True), start=2):
            raw_id, raw_name, raw_chance = row

            if raw_id is None and raw_name is None and raw_chance is None:
                continue

            if raw_id is None or raw_name is None or raw_chance is None:
                raise ValueError(f"Row {row_idx}: id/name/chance must be non-empty")

            item_id = str(raw_id).strip()
            name = str(raw_name).strip()
            if not item_id or not name:
                raise ValueError(f"Row {row_idx}: id/name must be non-empty")

            try:
                weight = float(raw_chance)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Row {row_idx}: chance must be float") from exc

            if not (0 < weight < 1):
                raise ValueError(f"Row {row_idx}: chance must satisfy 0 < chance < 1")

            if item_id in seen_ids:
                raise ValueError(f"Row {row_idx}: duplicate id '{item_id}'")
            seen_ids.add(item_id)

            icon_path = icons_dir / f"{item_id}.png"
            if not icon_path.exists():
                raise ValueError(f"Row {row_idx}: missing icon file {icon_path}")

            items.append(LootItem(item_id=item_id, name=name, weight=weight, icon_path=icon_path))

        if not items:
            raise ValueError("Excel contains no items")

        return cls(items)

    def pick_by_unit_random(self, r: float) -> LootItem:
        if not (0.0 <= r < 1.0):
            raise ValueError("r must be in [0, 1)")
        needle = r * self.total_weight
        idx = bisect.bisect_left(self._prefix_sums, needle)
        if idx >= len(self.items):
            idx = len(self.items) - 1
        return self.items[idx]

    def normalized_percent(self, item: LootItem) -> float:
        return (item.weight / self.total_weight) * 100.0
