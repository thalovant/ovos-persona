"""A persona may carry a ``fallback_response``, spoken when no handler answers.

Without one, behaviour is unchanged: ``chat`` returns whatever the solver chain
returned (possibly None) and ``stream`` yields what the chain yielded, and the
service speaks its generic ``persona_error`` dialog.
"""
from unittest.mock import MagicMock, patch

import pytest
from ovos_bus_client.session import Session

from ovos_persona import Persona
from ovos_persona.solvers import QuestionSolversService


class _Handler:
    def __init__(self, config=None):
        pass

    def shutdown(self):
        pass


def _persona(**extra):
    with patch("ovos_persona.solvers.get_utterance_handler_plugins",
               return_value={"dummy": _Handler}), \
         patch("ovos_persona.get_utterance_handler_plugins",
               return_value={"dummy": _Handler}), \
         patch("ovos_persona.load_memory_plugin", return_value=None):
        persona = Persona(name="test", config={"handlers": ["dummy"], **extra})
    persona.solvers = MagicMock(spec=QuestionSolversService)
    return persona


@pytest.fixture
def sess():
    return Session()


def test_no_fallback_means_no_change_on_chat(sess):
    persona = _persona()
    persona.solvers.chat_completion.return_value = None
    assert persona.fallback_response is None
    assert persona.chat(["hi"], sess) is None


def test_fallback_is_used_when_chat_gets_no_answer(sess):
    persona = _persona(fallback_response="  I cannot reach my brain right now.  ")
    persona.solvers.chat_completion.return_value = None
    assert persona.chat(["hi"], sess) == "I cannot reach my brain right now."


def test_a_real_answer_wins_over_the_fallback(sess):
    persona = _persona(fallback_response="fallback")
    persona.solvers.chat_completion.return_value = "the answer"
    assert persona.chat(["hi"], sess) == "the answer"


def test_fallback_is_used_when_the_stream_gives_nothing(sess):
    persona = _persona(fallback_response="fallback")
    persona.solvers.stream_completion.return_value = iter([])
    assert list(persona.stream(["hi"], sess)) == ["fallback"]


def test_empty_chunks_do_not_count_as_an_answer_on_stream(sess):
    persona = _persona(fallback_response="fallback")
    persona.solvers.stream_completion.return_value = iter([None, ""])
    assert list(persona.stream(["hi"], sess)) == [None, "", "fallback"]


def test_the_fallback_is_not_appended_after_a_real_stream(sess):
    persona = _persona(fallback_response="fallback")
    persona.solvers.stream_completion.return_value = iter(["one", "two"])
    assert list(persona.stream(["hi"], sess)) == ["one", "two"]


@pytest.mark.parametrize("value", ["", "   ", None, 7, ["x"]])
def test_blank_or_non_string_fallback_is_ignored(value, sess):
    persona = _persona(fallback_response=value)
    persona.solvers.stream_completion.return_value = iter([])
    assert persona.fallback_response is None
    assert list(persona.stream(["hi"], sess)) == []
