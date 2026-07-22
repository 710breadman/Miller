"""Typed audio inspection, alignment, comparison, and beat records."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AudioModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class AudioMetadata(AudioModel):
    path: str = Field(min_length=1)
    duration_seconds: float = Field(gt=0.0)
    codec: str = Field(min_length=1)
    sample_rate: int = Field(gt=0)
    channels: int = Field(gt=0)
    bit_rate: int | None = Field(default=None, gt=0)
    format_name: str = Field(min_length=1)
    ffprobe_version: str = Field(min_length=1)


class NormalizedAudio(AudioModel):
    source_path: str = Field(min_length=1)
    output_path: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    sample_rate: int = Field(default=16_000, gt=0)
    channels: int = Field(default=1, gt=0)
    codec: str = Field(default="pcm_s16le", min_length=1)
    ffmpeg_version: str = Field(min_length=1)
    command: tuple[str, ...]


class WordTiming(AudioModel):
    text: str = Field(min_length=1)
    start: float = Field(ge=0.0)
    end: float = Field(gt=0.0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    aligned: bool = True

    @model_validator(mode="after")
    def validate_range(self) -> WordTiming:
        if self.end <= self.start:
            raise ValueError("word timing end must be after start")
        return self


class AlignmentResult(AudioModel):
    engine: str = Field(min_length=1)
    engine_version: str = Field(min_length=1)
    model: str = Field(min_length=1)
    language: str = Field(min_length=2, max_length=32)
    audio_duration_seconds: float = Field(gt=0.0)
    words: tuple[WordTiming, ...]
    warnings: tuple[str, ...] = ()

    @field_validator("words")
    @classmethod
    def validate_words(cls, value: tuple[WordTiming, ...]) -> tuple[WordTiming, ...]:
        for previous, current in zip(value, value[1:], strict=False):
            if current.start < previous.end - 1e-6:
                raise ValueError("word timings must be monotonic and non-overlapping")
        return value

    @model_validator(mode="after")
    def validate_duration(self) -> AlignmentResult:
        if self.words and self.words[-1].end > self.audio_duration_seconds + 1e-3:
            raise ValueError("word timing exceeds audio duration")
        return self


class ScriptDifferenceKind(StrEnum):
    EQUAL = "equal"
    OMISSION = "omission"
    INSERTION = "insertion"
    SUBSTITUTION = "substitution"


class ScriptDifference(AudioModel):
    kind: ScriptDifferenceKind
    script_start: int = Field(ge=0)
    script_end: int = Field(ge=0)
    audio_start: int = Field(ge=0)
    audio_end: int = Field(ge=0)
    script_text: str = ""
    audio_text: str = ""


class ScriptComparison(AudioModel):
    differences: tuple[ScriptDifference, ...]
    script_word_count: int = Field(ge=0)
    audio_word_count: int = Field(ge=0)
    match_ratio: float = Field(ge=0.0, le=1.0)
    pickup_word_indexes: tuple[int, ...] = ()


class NarrationBeat(AudioModel):
    id: str = Field(pattern=r"^beat_[0-9]{4}$")
    section_index: int = Field(ge=0)
    start: float = Field(ge=0.0)
    end: float = Field(gt=0.0)
    text: str = Field(min_length=1)
    first_word_index: int = Field(ge=0)
    last_word_index: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_beat(self) -> NarrationBeat:
        if self.end <= self.start:
            raise ValueError("beat end must be after start")
        if self.last_word_index < self.first_word_index:
            raise ValueError("beat word range is reversed")
        return self


class BeatPlan(AudioModel):
    beats: tuple[NarrationBeat, ...]
    audio_duration_seconds: float = Field(gt=0.0)
    warnings: tuple[str, ...] = ()

    @field_validator("beats")
    @classmethod
    def validate_coverage(cls, value: tuple[NarrationBeat, ...]) -> tuple[NarrationBeat, ...]:
        if not value:
            raise ValueError("beat plan requires at least one beat")
        for previous, current in zip(value, value[1:], strict=False):
            if abs(current.start - previous.end) > 0.05:
                raise ValueError("beat plan contains a gap or overlap above tolerance")
            if current.first_word_index != previous.last_word_index + 1:
                raise ValueError("beat word ranges must be contiguous")
        return value
