from __future__ import annotations

from autopoietic.core.task import Task, ToolSpec

ACTION_FENCE = "action"


def render_tool_spec(tool: ToolSpec) -> str:
    return f"- {tool.name}: {tool.description}\n  args schema: {tool.parameters}"


EXAMPLE_TURN = (
    "Example turn, writing a two_sum solution:\n"
    f"```{ACTION_FENCE}\n"
    '{"tool": "write_file", "args": {"content": "def two_sum(nums, target):\\n'
    '    seen = {}\\n    for i, x in enumerate(nums):\\n'
    "        if target - x in seen:\\n"
    '            return [seen[target - x], i]\\n'
    "        seen[x] = i\\n"
    '"}}\n'
    "```\n"
    "Note the code is one JSON string with \\n for newlines - not a separate "
    f"```python block. A plain ```python code block is NOT an action and will "
    "be ignored."
)


def build_system_prompt(task: Task) -> str:
    tool_lines = "\n".join(render_tool_spec(t) for t in task.tools())
    return (
        f"{task.system_prompt()}\n\n"
        "You act by emitting exactly one action per turn as a fenced code block "
        "containing a single JSON object:\n"
        f"```{ACTION_FENCE}\n"
        '{"tool": "<tool_name>", "args": {...}}\n'
        "```\n"
        "Available tools:\n"
        f"{tool_lines}\n\n"
        f"{EXAMPLE_TURN}\n\n"
        "You may reason before the block, but every turn must end with exactly one "
        f"```{ACTION_FENCE}``` block calling one of the tools above. "
        "Nothing after the action block is read."
    )
