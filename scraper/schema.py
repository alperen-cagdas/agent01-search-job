from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    source: str
    posted_date: Optional[str] = None
    description_snippet: str = ""
    score: float = 0.0
    matched_keywords: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
