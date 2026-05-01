"""Util that calls the UniRate API for currency exchange rates and conversions."""

from __future__ import annotations

from typing import Any

import requests
from langchain_core.utils import secret_from_env
from pydantic import BaseModel, ConfigDict, Field, SecretStr


class UniRateAPIWrapper(BaseModel):
    """Wrapper for the UniRate API (https://unirateapi.com).

    UniRate provides 593+ fiat, crypto, and commodity exchange rates with a
    permissive free tier. Latest rates and conversion are free; historical
    endpoints require a Pro plan.

    Setup:

    1. Sign up at https://unirateapi.com to get an API key.
    2. Save the key into the ``UNIRATE_API_KEY`` environment variable
       (or pass ``unirate_api_key`` directly when constructing the wrapper).

    Example:
        .. code-block:: python

            from langchain_unirate import UniRateAPIWrapper

            wrapper = UniRateAPIWrapper()
            print(wrapper.convert("USD", "EUR", amount=100))
            print(wrapper.get_rate("USD", "GBP"))
            print(wrapper.get_supported_currencies()[:5])
    """

    unirate_api_key: SecretStr = Field(
        default_factory=secret_from_env(["UNIRATE_API_KEY"]),
    )
    """API key for the UniRate API.

    Read from the ``UNIRATE_API_KEY`` environment variable when not passed
    explicitly.
    """
    base_url: str = "https://api.unirateapi.com"
    request_timeout: int = 30

    model_config = ConfigDict(
        extra="forbid",
    )

    def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        """Send a GET request to the UniRate API and parse the JSON body.

        ``Accept: application/json`` is required by the API — without it
        ``/api/currencies`` returns an HTML 404.
        """
        full_params = {**params, "api_key": self.unirate_api_key.get_secret_value()}
        response = requests.get(
            f"{self.base_url}{path}",
            params=full_params,
            headers={"Accept": "application/json"},
            timeout=self.request_timeout,
        )
        if response.status_code == 401:
            msg = "Missing or invalid UniRate API key"
            raise ValueError(msg)
        if response.status_code == 403:
            msg = "Endpoint requires a UniRate Pro subscription"
            raise ValueError(msg)
        if response.status_code == 404:
            msg = "Currency not found or no data available"
            raise ValueError(msg)
        if response.status_code == 429:
            msg = "UniRate API rate limit exceeded"
            raise ValueError(msg)
        response.raise_for_status()
        return response.json()

    def get_rate(
        self,
        from_currency: str = "USD",
        to_currency: str | None = None,
    ) -> float | dict[str, float]:
        """Get the current exchange rate for a currency pair, or all rates.

        Args:
            from_currency: ISO 4217 base currency code.
            to_currency: ISO 4217 target currency code. If omitted, returns a
                mapping of every supported target to its rate.

        Returns:
            A single ``float`` rate when ``to_currency`` is provided, otherwise
            a ``dict`` mapping every target currency code to its rate.
        """
        params: dict[str, Any] = {"from": from_currency.upper()}
        if to_currency is not None:
            params["to"] = to_currency.upper()
        data = self._request("/api/rates", params)
        if to_currency is not None:
            return float(data["rate"])
        return {code: float(rate) for code, rate in data["rates"].items()}

    def convert(
        self,
        from_currency: str,
        to_currency: str,
        amount: float = 1.0,
    ) -> float:
        """Convert an amount from one currency to another at the latest rate.

        Args:
            from_currency: ISO 4217 source currency code.
            to_currency: ISO 4217 target currency code.
            amount: The amount of ``from_currency`` to convert.

        Returns:
            The converted amount as a ``float``.
        """
        data = self._request(
            "/api/convert",
            {
                "from": from_currency.upper(),
                "to": to_currency.upper(),
                "amount": amount,
            },
        )
        return float(data["result"])

    def get_supported_currencies(self) -> list[str]:
        """Return the list of supported currency codes.

        Returns:
            The list of ISO 4217 (fiat) and ticker (crypto, commodity) codes
            that the UniRate API can convert between.
        """
        data = self._request("/api/currencies", {})
        return list(data["currencies"])

    def run(
        self,
        from_currency: str,
        to_currency: str,
        amount: float = 1.0,
    ) -> str:
        """Convert an amount and format the result for an LLM agent.

        Args:
            from_currency: ISO 4217 source currency code.
            to_currency: ISO 4217 target currency code.
            amount: The amount of ``from_currency`` to convert.

        Returns:
            A short human-readable sentence with the converted amount.
        """
        result = self.convert(from_currency, to_currency, amount)
        return (
            f"{amount} {from_currency.upper()} = "
            f"{result} {to_currency.upper()} (UniRate latest rate)"
        )
