"""Shared type aliases for the Gaffer API."""

from typing import Literal, TypeAlias

ManagerStyle: TypeAlias = Literal["ferguson", "klopp", "guardiola", "mourinho", "bielsa"]
HypeStatus: TypeAlias = Literal["pending", "text_ready", "audio_ready", "error"]
PlanType: TypeAlias = Literal["free", "pro"]
