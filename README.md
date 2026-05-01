# langchain-unirate

[![PyPI](https://img.shields.io/pypi/v/langchain-unirate.svg)](https://pypi.org/project/langchain-unirate/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

LangChain integration for the [UniRate API](https://unirateapi.com) — drop-in
currency-exchange tooling for LangChain agents and chains.

UniRate provides 593+ fiat, crypto, and commodity exchange rates. Latest rates
and conversions are available on the free tier; historical and time-series
endpoints require a Pro plan.

## Why this package

There's no first-class FX tool in core LangChain — most tutorials show users
hand-rolling one against `exchangerate-api.com` or AlphaVantage. This package
gives you a typed, tested wrapper plus a ready-to-use `BaseTool` that an agent
can call directly via tool-calling.

## Install

```bash
pip install langchain-unirate
```

## Quick start

```python
import os

os.environ["UNIRATE_API_KEY"] = "..."  # https://unirateapi.com

from langchain_unirate import UniRateAPIWrapper, UniRateExchangeTool

wrapper = UniRateAPIWrapper()

# Direct API
print(wrapper.convert("USD", "EUR", amount=100))    # 92.5
print(wrapper.get_rate("USD", "GBP"))               # 0.79
print(wrapper.get_supported_currencies()[:5])

# As an agent tool
tool = UniRateExchangeTool(api_wrapper=wrapper)
tool.invoke({"from_currency": "USD", "to_currency": "EUR", "amount": 100})
# -> "100 USD = 92.5 EUR (UniRate latest rate)"
```

## Use with an agent

```python
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent

from langchain_unirate import UniRateAPIWrapper, UniRateExchangeTool

tool = UniRateExchangeTool(api_wrapper=UniRateAPIWrapper())
agent = create_react_agent(init_chat_model("openai:gpt-4o-mini"), tools=[tool])

agent.invoke({"messages": [("user", "How many euros is 250 dollars right now?")]})
```

## API

### `UniRateAPIWrapper`

| Method | Returns | Description |
|---|---|---|
| `get_rate(from_currency="USD", to_currency=None)` | `float` or `dict[str, float]` | Latest rate; if `to_currency` is omitted, returns every supported target. |
| `convert(from_currency, to_currency, amount=1.0)` | `float` | Convert `amount` at the latest rate. |
| `get_supported_currencies()` | `list[str]` | All currency codes UniRate can convert between. |
| `run(from_currency, to_currency, amount=1.0)` | `str` | Agent-friendly formatter wrapping `convert`. |

### `UniRateExchangeTool`

`BaseTool` with a structured `args_schema` over (`from_currency`,
`to_currency`, `amount`). Compatible with any LangChain tool-calling pattern:
`bind_tools()`, `create_react_agent`, ToolNode, etc.

## Configuration

| Constructor arg | Env var | Default |
|---|---|---|
| `unirate_api_key` | `UNIRATE_API_KEY` | — (required) |
| `base_url` | — | `https://api.unirateapi.com` |
| `request_timeout` | — | `30` (seconds) |

Errors map cleanly to `ValueError` for `401` / `403` / `404` / `429`; other
non-2xx responses raise `requests.HTTPError`.

## Related UniRate clients

If you want to call the API directly from a non-Python application, there are
official clients in
[Python](https://github.com/UniRate-API/unirate-api-python),
[Node.js](https://github.com/UniRate-API/unirate-api-nodejs),
[Go](https://github.com/UniRate-API/unirate-api-go),
[Rust](https://github.com/UniRate-API/unirate-api-rust),
[Java](https://github.com/UniRate-API/unirate-api-java),
[Ruby](https://github.com/UniRate-API/unirate-api-ruby),
[PHP](https://github.com/UniRate-API/unirate-api-php),
[.NET](https://github.com/UniRate-API/unirate-api-dotnet), and
[Swift](https://github.com/UniRate-API/unirate-api-swift), as well as an
[MCP server](https://github.com/UniRate-API/unirate-mcp) for Claude Desktop and
other MCP hosts.

## License

MIT — see [LICENSE](LICENSE).
