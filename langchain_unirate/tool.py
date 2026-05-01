"""LangChain tool wrapping the UniRate currency exchange API."""

from __future__ import annotations

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from langchain_unirate.utility import UniRateAPIWrapper


class UniRateExchangeInput(BaseModel):
    """Input schema for ``UniRateExchangeTool``."""

    from_currency: str = Field(
        description=(
            "The ISO 4217 source currency code (e.g. 'USD', 'EUR'). "
            "Crypto and commodity tickers are also supported (e.g. 'BTC', 'XAU')."
        ),
    )
    to_currency: str = Field(
        description="The ISO 4217 target currency code to convert into.",
    )
    amount: float = Field(
        default=1.0,
        description="The amount of the source currency to convert. Defaults to 1.",
    )


class UniRateExchangeTool(BaseTool):
    """Tool that converts an amount between currencies using the UniRate API.

    Useful when an agent needs current foreign-exchange rates or needs to
    convert a monetary amount from one currency to another. Supports 593+
    fiat, crypto, and commodity instruments.

    Setup:

    1. Sign up at https://unirateapi.com to obtain an API key.
    2. Save the key into the ``UNIRATE_API_KEY`` environment variable
       (or pass ``api_wrapper=UniRateAPIWrapper(unirate_api_key=...)`` at
       construction time).

    Example:
        .. code-block:: python

            from langchain_unirate import UniRateAPIWrapper, UniRateExchangeTool

            tool = UniRateExchangeTool(api_wrapper=UniRateAPIWrapper())
            tool.invoke({"from_currency": "USD", "to_currency": "EUR", "amount": 100})
    """

    name: str = "unirate_exchange"
    description: str = (
        "A wrapper around the UniRate currency exchange API. "
        "Useful for converting an amount from one currency to another at the "
        "current market rate, or for looking up the latest exchange rate "
        "between two currencies. "
        "Input requires a source currency code, a target currency code, and "
        "an amount (defaults to 1)."
    )
    args_schema: type[BaseModel] = UniRateExchangeInput  # type: ignore[assignment]
    api_wrapper: UniRateAPIWrapper

    def _run(
        self,
        from_currency: str,
        to_currency: str,
        amount: float = 1.0,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        """Use the UniRate API to convert ``amount`` from one currency to another."""
        return self.api_wrapper.run(
            from_currency=from_currency,
            to_currency=to_currency,
            amount=amount,
        )
