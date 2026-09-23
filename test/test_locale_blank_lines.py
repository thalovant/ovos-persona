"""The blank line that took the whole pipeline plugin down.

`load_resource_files` splits each locale file on "\n", so a file ending with a
newline -- which most editors write -- hands `load_intent_files` a final empty
sample. `expand_template("")` raises MalformedTemplate, and that call used to
sit outside the per-intent try/except, so one stray blank line did not skip one
intent: it aborted the whole of `load_intent_files`. The plugin then failed to
construct, and ovos-core filtered `ovos-persona-pipeline-plugin-high` and
`-low` out of every pipeline that asked for them, for every language.

Twelve of this package's own files ended with a newline (fr, ca, gl, it).
test_locale_templates.py did not catch it because it calls `line.strip()` and
`continue`s on a falsy line -- it skips precisely the input that breaks
production. These tests read the files the way production does.
"""
import os
import unittest

from ovos_persona import PersonaService

PACKAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "ovos_persona")
LOCALE_ROOT = os.path.join(PACKAGE_DIR, "locale")
TEMPLATE_EXTENSIONS = (".voc", ".intent")


def iter_template_files():
    for root, _dirs, files in os.walk(LOCALE_ROOT):
        for fname in sorted(files):
            if fname.endswith(TEMPLATE_EXTENSIONS):
                yield os.path.join(root, fname)


class TestShippedLocaleFiles(unittest.TestCase):
    def test_no_template_file_ends_with_a_newline(self):
        """The data half of the fix, and the guard against it coming back."""
        offenders = []
        for path in iter_template_files():
            with open(path, "rb") as f:
                content = f.read()
            if content.endswith(b"\n"):
                offenders.append(os.path.relpath(path, PACKAGE_DIR))
        self.assertEqual(
            offenders, [],
            "these files end with a newline, so read().split('\\n') yields a "
            "trailing empty sample:\n" + "\n".join(offenders))

    def test_every_shipped_file_survives_the_production_reader(self):
        """Read and expand exactly as load_resource_files/load_intent_files do."""
        for path in iter_template_files():
            with open(path) as f:
                lines = f.read().split("\n")
            lines = [s.replace("{{", "{").replace("}}", "}") for s in lines]
            rel = os.path.relpath(path, PACKAGE_DIR)
            try:
                PersonaService._samples_for(lines, lang="test", intent_name=rel)
            except Exception as error:  # pragma: no cover - the failure we fixed
                self.fail(f"{rel} raised {type(error).__name__}: {error}")


class TestSamplesFor(unittest.TestCase):
    def test_a_trailing_blank_line_is_dropped_not_fatal(self):
        samples = PersonaService._samples_for(
            ["hello {persona}", ""], lang="en-US", intent_name="ask.intent")
        self.assertEqual(samples, ["hello {persona}"])

    def test_blank_and_whitespace_only_lines_are_ignored(self):
        samples = PersonaService._samples_for(
            ["", "   ", "\t", "ask {persona}"], lang="en-US", intent_name="ask.intent")
        self.assertEqual(samples, ["ask {persona}"])

    def test_one_malformed_template_does_not_cost_the_others(self):
        """A bad sentence in one translation must not disarm every language."""
        samples = PersonaService._samples_for(
            ["good {persona}", "(unclosed", "also good {persona}"],
            lang="en-US", intent_name="ask.intent")
        self.assertIn("good {persona}", samples)
        self.assertIn("also good {persona}", samples)

    def test_brackets_still_expand(self):
        samples = PersonaService._samples_for(
            ["(hi|hello) {persona}"], lang="en-US", intent_name="ask.intent")
        self.assertEqual(sorted(samples), ["hello {persona}", "hi {persona}"])


if __name__ == "__main__":
    unittest.main()
