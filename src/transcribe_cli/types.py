from dataclasses import dataclass, field
from typing import Any


@dataclass
class Word:
    start: float
    end: float
    word: str
    probability: float = 1.0


@dataclass
class Segment:
    id: int
    start: float
    end: float
    text: str
    avg_logprob: float = 0.0
    no_speech_prob: float = 0.0
    words: list[Word] = field(default_factory=list)


@dataclass
class Transcript:
    language: str
    language_probability: float
    duration: float
    model: str
    settings: dict[str, Any]
    segments: list[Segment] = field(default_factory=list)


@dataclass
class Cue:
    start: float
    end: float
    text: str
