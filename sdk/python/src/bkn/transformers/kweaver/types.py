# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Kweaver import result and error types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


class KweaverImportError(Exception):
    """Raised when kweaver API returns a non-2xx response."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_text: str = "",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


@dataclass
class ImportResult:
    """Result of importing a BKN network into kweaver."""

    knowledge_network_id: str = ""
    object_types_created: int = 0
    relation_types_created: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """True if no errors occurred."""
        return len(self.errors) == 0