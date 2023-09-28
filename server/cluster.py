from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Cluster():
    name: str
    path: str
    preview: Optional[str] = None
    items: set[str] = field(default_factory=set)
