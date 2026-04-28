# Copyright The kweaver.ai Authors.
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Base transformer for converting BKN models to platform-specific formats."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bkn.models import BknNetwork


class Transformer(ABC):
    """Abstract base class for BKN network transformers.

    Subclasses implement platform-specific conversion logic.
    """

    @abstractmethod
    def to_json(self, network: "BknNetwork") -> dict[str, Any]:
        """Transform a BKN network to platform-specific JSON.

        Args:
            network: The BKN network to transform.

        Returns:
            Dict with platform-specific structure (keys depend on implementation).
        """
        ...

    @abstractmethod
    def to_files(
        self,
        network: "BknNetwork",
        output_dir: str | Path,
        indent: int = 2,
    ) -> list[Path]:
        """Write transformed output to files.

        Args:
            network: The BKN network to transform.
            output_dir: Directory to write files into.
            indent: JSON indent for pretty-printing.

        Returns:
            List of created file paths.
        """
        ...