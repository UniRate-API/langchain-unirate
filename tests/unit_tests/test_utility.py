"""Unit tests for ``UniRateAPIWrapper``."""

from typing import Any

import pytest
import requests
import requests_mock as requests_mock_lib
from pydantic import SecretStr

from langchain_unirate import UniRateAPIWrapper

BASE_URL = "https://api.unirateapi.com"


def _wrapper() -> UniRateAPIWrapper:
    return UniRateAPIWrapper(unirate_api_key=SecretStr("test-key"))


def test_api_key_explicit() -> None:
    wrapper = _wrapper()
    assert wrapper.unirate_api_key.get_secret_value() == "test-key"


def test_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UNIRATE_API_KEY", "env-key")
    wrapper = UniRateAPIWrapper()
    assert wrapper.unirate_api_key.get_secret_value() == "env-key"


def test_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("UNIRATE_API_KEY", raising=False)
    with pytest.raises(ValueError):
        UniRateAPIWrapper()


def test_get_rate_pair(requests_mock: requests_mock_lib.Mocker) -> None:
    requests_mock.get(f"{BASE_URL}/api/rates", json={"rate": "0.92"})
    rate = _wrapper().get_rate("USD", "EUR")
    assert rate == pytest.approx(0.92)
    request = requests_mock.last_request
    assert request is not None
    assert request.qs["from"] == ["usd"]
    assert request.qs["to"] == ["eur"]
    assert request.qs["api_key"] == ["test-key"]
    assert request.headers.get("Accept") == "application/json"


def test_get_rate_uppercases_inputs(
    requests_mock: requests_mock_lib.Mocker,
) -> None:
    requests_mock.get(f"{BASE_URL}/api/rates", json={"rate": "0.79"})
    _wrapper().get_rate("usd", "gbp")
    request = requests_mock.last_request
    assert request is not None
    assert request.qs["from"] == ["usd"]
    assert request.qs["to"] == ["gbp"]


def test_get_rate_all_targets(requests_mock: requests_mock_lib.Mocker) -> None:
    requests_mock.get(
        f"{BASE_URL}/api/rates",
        json={"rates": {"EUR": "0.92", "GBP": "0.79"}},
    )
    rates = _wrapper().get_rate("USD")
    assert rates == {"EUR": pytest.approx(0.92), "GBP": pytest.approx(0.79)}
    request = requests_mock.last_request
    assert request is not None
    assert "to" not in request.qs


def test_convert(requests_mock: requests_mock_lib.Mocker) -> None:
    requests_mock.get(f"{BASE_URL}/api/convert", json={"result": "92.50"})
    result = _wrapper().convert("USD", "EUR", amount=100)
    assert result == pytest.approx(92.50)
    request = requests_mock.last_request
    assert request is not None
    assert request.qs["amount"] == ["100"]


def test_get_supported_currencies(
    requests_mock: requests_mock_lib.Mocker,
) -> None:
    requests_mock.get(
        f"{BASE_URL}/api/currencies",
        json={"currencies": ["USD", "EUR", "GBP"]},
    )
    assert _wrapper().get_supported_currencies() == ["USD", "EUR", "GBP"]


def test_run_formats_for_agent(
    requests_mock: requests_mock_lib.Mocker,
) -> None:
    requests_mock.get(f"{BASE_URL}/api/convert", json={"result": "92.50"})
    output = _wrapper().run("usd", "eur", amount=100)
    assert "100" in output
    assert "USD" in output
    assert "EUR" in output
    assert "92.5" in output


@pytest.mark.parametrize(
    ("status_code", "fragment"),
    [
        (401, "invalid"),
        (403, "Pro"),
        (404, "not found"),
        (429, "rate limit"),
    ],
)
def test_error_mapping(
    requests_mock: requests_mock_lib.Mocker,
    status_code: int,
    fragment: str,
) -> None:
    requests_mock.get(
        f"{BASE_URL}/api/rates",
        status_code=status_code,
        json={"error": "boom"},
    )
    with pytest.raises(ValueError, match=fragment):
        _wrapper().get_rate("USD", "EUR")


def test_other_http_error_raises(
    requests_mock: requests_mock_lib.Mocker,
) -> None:
    requests_mock.get(
        f"{BASE_URL}/api/rates",
        status_code=503,
        json={"error": "unavailable"},
    )
    with pytest.raises(requests.HTTPError):
        _wrapper().get_rate("USD", "EUR")


def test_extra_field_rejected() -> None:
    with pytest.raises(ValueError):
        UniRateAPIWrapper(
            unirate_api_key=SecretStr("k"),
            unexpected_field="x",  # type: ignore[call-arg]
        )


def test_secret_value_not_in_repr() -> None:
    wrapper = _wrapper()
    assert "test-key" not in repr(wrapper)


def test_request_timeout_passed_through(
    requests_mock: requests_mock_lib.Mocker,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests_mock.get(f"{BASE_URL}/api/rates", json={"rate": "1.0"})
    captured: dict[str, Any] = {}
    original_get = requests.get

    def spy_get(*args: Any, **kwargs: Any) -> Any:
        captured["timeout"] = kwargs.get("timeout")
        return original_get(*args, **kwargs)

    monkeypatch.setattr(requests, "get", spy_get)
    UniRateAPIWrapper(
        unirate_api_key=SecretStr("test-key"),
        request_timeout=7,
    ).get_rate("USD", "EUR")
    assert captured["timeout"] == 7
