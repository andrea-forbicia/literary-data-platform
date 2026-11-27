import pytest

from literary_data_platform.config import MissingSettingError, require_env


def test_returns_value_without_surrounding_spaces():
    assert require_env("DATA_DIR", {"DATA_DIR": " data "}) == "data"


@pytest.mark.parametrize("environ", [{}, {"DATA_DIR": ""}, {"DATA_DIR": "   "}])
def test_missing_or_empty_value_is_an_error(environ):
    with pytest.raises(MissingSettingError, match="DATA_DIR"):
        require_env("DATA_DIR", environ)
