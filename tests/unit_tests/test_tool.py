"""Unit tests for ``UniRateExchangeTool``."""

import requests_mock as requests_mock_lib
from pydantic import SecretStr

from langchain_unirate import UniRateAPIWrapper, UniRateExchangeTool

BASE_URL = "https://api.unirateapi.com"


def _tool() -> UniRateExchangeTool:
    return UniRateExchangeTool(
        api_wrapper=UniRateAPIWrapper(unirate_api_key=SecretStr("test-key"))
    )


def test_invoke_uses_api_wrapper(
    requests_mock: requests_mock_lib.Mocker,
) -> None:
    requests_mock.get(f"{BASE_URL}/api/convert", json={"result": "92.50"})
    output = _tool().invoke(
        {"from_currency": "USD", "to_currency": "EUR", "amount": 100}
    )
    assert "100" in output
    assert "EUR" in output
    request = requests_mock.last_request
    assert request is not None
    assert request.qs["from"] == ["usd"]
    assert request.qs["to"] == ["eur"]
    assert request.qs["amount"] == ["100.0"]


def test_default_amount_is_one(
    requests_mock: requests_mock_lib.Mocker,
) -> None:
    requests_mock.get(f"{BASE_URL}/api/convert", json={"result": "0.92"})
    _tool().invoke({"from_currency": "USD", "to_currency": "EUR"})
    request = requests_mock.last_request
    assert request is not None
    assert request.qs["amount"] == ["1.0"]


def test_args_schema_is_set() -> None:
    tool = _tool()
    assert tool.args_schema is not None
    fields = tool.args_schema.model_fields
    assert set(fields.keys()) == {"from_currency", "to_currency", "amount"}


def test_tool_name_and_description() -> None:
    tool = _tool()
    assert tool.name == "unirate_exchange"
    assert "currency" in tool.description.lower()


def test_top_level_imports() -> None:
    from langchain_unirate import (
        UniRateAPIWrapper,
        UniRateExchangeInput,
        UniRateExchangeTool,
    )

    assert UniRateAPIWrapper.__name__ == "UniRateAPIWrapper"
    assert UniRateExchangeTool.__name__ == "UniRateExchangeTool"
    assert UniRateExchangeInput.__name__ == "UniRateExchangeInput"
