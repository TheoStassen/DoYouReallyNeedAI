from dataclasses import dataclass, field
import uuid

@dataclass
class Question:
    """Simple Question model with a stable id and text."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""
    description: str = ""

@dataclass
class Answer:
    """Simple Answer model with a stable id and text."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text: str = ""

