import pytest

from autopoietic.agent.tools import ActionParseError, parse_action


def test_parse_simple_action():
    text = '```action\n{"tool": "submit", "args": {}}\n```'
    tool, args = parse_action(text)
    assert tool == "submit"
    assert args == {}


def test_parse_with_reasoning_prefix():
    text = 'Let me think about this.\n```action\n{"tool": "write_file", "args": {"content": "x"}}\n```'
    tool, args = parse_action(text)
    assert tool == "write_file"
    assert args == {"content": "x"}


def test_parse_takes_last_block():
    text = (
        '```action\n{"tool": "run_tests", "args": {}}\n```\n'
        'actually wait\n'
        '```action\n{"tool": "submit", "args": {}}\n```'
    )
    tool, _ = parse_action(text)
    assert tool == "submit"


def test_no_action_raises():
    with pytest.raises(ActionParseError):
        parse_action("just some text, no block here")


def test_invalid_json_raises():
    with pytest.raises(ActionParseError):
        parse_action("```action\nnot json\n```")


def test_missing_tool_key_raises():
    with pytest.raises(ActionParseError):
        parse_action('```action\n{"args": {}}\n```')
