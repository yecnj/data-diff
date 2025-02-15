from dataclasses import field
from typing import List, Dict, Optional, Any, Tuple, Union

from runtype import dataclass

from .table_segment import TableSegment


@dataclass(frozen=False)
class SegmentInfo:
    tables: List[TableSegment]

    diff: List[Union[Tuple[Any, ...], List[Any]]] = None
    diff_schema: Tuple[Tuple[str, type], ...] = None
    is_diff: bool = None
    diff_count: int = None

    rowcounts: Dict[int, int] = field(default_factory=dict)
    max_rows: int = None

    def set_diff(self, diff: List[Union[Tuple[Any, ...], List[Any]]], schema: Optional[Tuple[Tuple[str, type]]] = None):
        self.diff_schema = schema
        self.diff = diff
        self.diff_count = len(diff)
        self.is_diff = self.diff_count > 0

    def update_from_children(self, child_infos):
        child_infos = list(child_infos)
        assert child_infos

        # self.diff = list(chain(*[c.diff for c in child_infos]))
        self.diff_count = sum(c.diff_count for c in child_infos if c.diff_count is not None)
        self.is_diff = any(c.is_diff for c in child_infos)
        self.diff_schema = next((child.diff_schema for child in child_infos if child.diff_schema is not None), None)
        self.diff = sum((c.diff for c in child_infos if c.diff is not None), [])

        self.rowcounts = {
            1: sum(c.rowcounts[1] for c in child_infos if c.rowcounts),
            2: sum(c.rowcounts[2] for c in child_infos if c.rowcounts),
        }


@dataclass
class InfoTree:
    info: SegmentInfo
    children: List["InfoTree"] = field(default_factory=list)

    def add_node(self, table1: TableSegment, table2: TableSegment, max_rows: int = None):
        node = InfoTree(SegmentInfo([table1, table2], max_rows=max_rows))
        self.children.append(node)
        return node

    def aggregate_info(self):
        if self.children:
            for c in self.children:
                c.aggregate_info()
            self.info.update_from_children(c.info for c in self.children)
