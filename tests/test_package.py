import importlib

import pytest

SUBPACKAGES = ["ingestion", "transform", "quality", "ai", "api"]


@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackage_is_importable(name: str) -> None:
    importlib.import_module(f"literary_data_platform.{name}")
