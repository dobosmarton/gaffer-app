"""Shared type aliases for the Gaffer API."""

from typing import Literal

type ManagerStyle = Literal["ferguson", "klopp", "guardiola", "mourinho", "bielsa"]
type HypeStatus = Literal["pending", "text_ready", "audio_ready", "error"]
type PlanType = Literal["free", "pro"]
