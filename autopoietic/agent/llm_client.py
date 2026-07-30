from __future__ import annotations

from typing import Protocol

from autopoietic.core.trajectory import Message


class ChatClient(Protocol):
    def generate(self, messages: list[Message]) -> str: ...


def to_chat_dicts(messages: list[Message]) -> list[dict[str, str]]:
    """Map our Message roles onto plain chat-template roles. Tool results are
    surfaced as user turns (prefixed) rather than a native 'tool' role: the
    agent uses a custom text action protocol instead of a model's native
    function-calling, so this keeps behavior identical across any small
    open-weight chat model regardless of its template's tool-role support."""
    out: list[dict[str, str]] = []
    for m in messages:
        if m.role == "tool":
            out.append(
                {"role": "user", "content": f"[tool result: {m.tool_name}]\n{m.content}"}
            )
        else:
            out.append({"role": m.role, "content": m.content})
    return out


class MLXClient:
    """ChatClient backed by mlx-lm, running in-process on Apple Silicon.
    Swapping adapters between fine-tune cycles = constructing a new
    MLXClient with a different adapter_path, not a network call."""

    def __init__(
        self,
        model_path: str,
        adapter_path: str | None = None,
        max_tokens: int = 512,
        temp: float = 0.0,
    ):
        from mlx_lm import load

        self.model_path = model_path
        self.adapter_path = adapter_path
        self.max_tokens = max_tokens
        self.temp = temp
        self.model, self.tokenizer = load(model_path, adapter_path=adapter_path)

    def generate(self, messages: list[Message]) -> str:
        from mlx_lm import generate
        from mlx_lm.sample_utils import make_sampler

        prompt = self.tokenizer.apply_chat_template(
            to_chat_dicts(messages),
            tokenize=False,
            add_generation_prompt=True,
        )
        sampler = make_sampler(temp=self.temp)
        return generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            max_tokens=self.max_tokens,
            sampler=sampler,
        )
