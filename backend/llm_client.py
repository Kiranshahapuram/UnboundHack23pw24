"""
Unbound API integration - centralized LLM client.
implements retries, timeouts, and clean error propagation.
"""

import time
import httpx
from typing import Tuple
from config import settings


AVAILABLE_MODELS = ("kimi-k2p5", "kimi-k2-instruct-0905")
MODEL_COSTS = {
    "kimi-k2p5": {"input": 0.0003, "output": 0.0012},
    "kimi-k2-instruct-0905": {"input": 0.0003, "output": 0.0012},
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    costs = MODEL_COSTS.get(model, MODEL_COSTS["kimi-k2p5"])
    return (input_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"])


async def call_llm(
    messages: list[dict],
    model: str = "kimi-k2p5",
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> Tuple[str, int, int, float, int]:
    """
    Call Unbound API with infra-level hardening.
    Returns: (content, input_tokens, output_tokens, cost_usd, latency_ms)
    """

    url = f"{settings.unbound_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.unbound_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    last_error = None
    start = time.perf_counter()

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, read=30.0)
            ) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()

            latency_ms = int((time.perf_counter() - start) * 1000)

            data = resp.json()
            choice = data.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "") or ""

            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            cost = _estimate_cost(model, input_tokens, output_tokens)

            return content, input_tokens, output_tokens, cost, latency_ms

        except (httpx.ReadError, httpx.TimeoutException, httpx.ConnectError) as e:
            last_error = e
            if attempt == 1:
                break
            await httpx.AsyncClient().aclose()

        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Unbound API HTTP error {e.response.status_code}: {e.response.text}"
            ) from e

        except Exception as e:
            raise RuntimeError(f"Unbound client error: {repr(e)}") from e

    raise RuntimeError(f"Unbound transport failure after retry: {repr(last_error)}")
