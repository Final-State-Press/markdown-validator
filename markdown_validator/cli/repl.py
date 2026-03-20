"""Interactive REPL for developing and testing validation rules.

Provides a :class:`ValidatorREPL` class (``cmd.Cmd`` subclass) that lets
developers probe documents interactively without writing a full rule set.

Start the REPL::

    python -m markdown_validator.cli.repl

or via the CLI::

    md-validate repl
"""

from __future__ import annotations

import cmd
import json
import logging
import shlex
import sys

from markdown_validator.domain.evaluator import _xpath_query, evaluate_rule
from markdown_validator.domain.models import ParsedDocument, RuleModel
from markdown_validator.infrastructure.parser import parse_document

logger = logging.getLogger(__name__)

_PROMPT = "> "
_INTRO = (
    "Markdown Validator REPL\n"
    "Type 'help' for a list of commands, 'quit' to exit.\n"
)


class ValidatorREPL(cmd.Cmd):
    """Interactive REPL for exploring and testing validation rules.

    :cvar intro: Introductory message displayed on startup.
    :cvar prompt: Shell prompt string.
    """

    intro: str = _INTRO
    prompt: str = _PROMPT

    def __init__(self) -> None:
        super().__init__()
        self._doc: ParsedDocument | None = None

    # ------------------------------------------------------------------
    # Document loading
    # ------------------------------------------------------------------

    def do_load(self, line: str) -> None:
        """Load a Markdown file for subsequent queries.

        Usage: load <path-to-markdown-file>
        """
        parts = shlex.split(line)
        if not parts:
            print("Usage: load <path-to-markdown-file>")
            return
        path = parts[0]
        try:
            self._doc = parse_document(path)
            print(f"Loaded: {self._doc.filepath}")
            print(f"  Metadata keys : {list(self._doc.metadata.keys())}")
        except (FileNotFoundError, ValueError) as exc:
            print(f"Error: {exc}")

    def do_dump(self, line: str) -> None:
        """Dump document content.  Options: metadata | html | raw

        Usage: dump metadata
               dump html
        """
        if self._doc is None:
            print("No document loaded. Use: load <path>")
            return
        arg = line.strip().lower()
        if arg == "metadata":
            print(json.dumps(self._doc.metadata, indent=2))
        elif arg == "html":
            print(self._doc.html)
        else:
            print("Usage: dump metadata | html")

    # ------------------------------------------------------------------
    # XPath queries
    # ------------------------------------------------------------------

    def do_query(self, line: str) -> None:
        """Run an XPath query against the loaded document.

        Usage: query <xpath> [flag]

        Flags: text (default), count, dom
        Example: query /html/body/h1 text
                 query /html/body/h2 count
        """
        if self._doc is None:
            print("No document loaded. Use: load <path>")
            return
        parts = shlex.split(line)
        if not parts:
            print("Usage: query <xpath> [flag]")
            return
        xpath = parts[0]
        flag = parts[1] if len(parts) > 1 else "text"
        result = _xpath_query(self._doc.html, xpath, flag)
        print(f"Result: {result}")

    # ------------------------------------------------------------------
    # Rule evaluation
    # ------------------------------------------------------------------

    def do_eval(self, line: str) -> None:
        """Evaluate a rule JSON payload against the loaded document.

        Usage: eval <json-rule-object>

        Example:
            eval {"name":"check-h1","id":1,"type":"body","query":"/html/body/h1","flag":"count","operation":"==","value":"1"}
        """
        if self._doc is None:
            print("No document loaded. Use: load <path>")
            return
        try:
            data = json.loads(line)
            rule = RuleModel.model_validate(data)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"Invalid rule JSON: {exc}")
            return
        result = evaluate_rule(rule, self._doc)
        status = "PASS" if result.passed else "FAIL"
        print(f"{status}: rule id={result.rule_id} name={result.rule_name!r}")
        if not result.passed and result.mitigation:
            print(f"  → {result.mitigation}")

    def do_get(self, line: str) -> None:
        """Get a metadata value by key.

        Usage: get <metadata-key>
        Example: get ms.topic
        """
        if self._doc is None:
            print("No document loaded. Use: load <path>")
            return
        key = line.strip()
        value = self._doc.metadata.get(key)
        if value is None:
            print(f"Key {key!r} not found in metadata.")
        else:
            print(f"{key}: {value}")

    # ------------------------------------------------------------------
    # Exit commands
    # ------------------------------------------------------------------

    def do_quit(self, _line: str) -> bool:
        """Exit the REPL."""
        return True

    def do_exit(self, line: str) -> bool:
        """Exit the REPL."""
        return self.do_quit(line)

    def do_EOF(self, line: str) -> bool:  # noqa: N802  (cmd.Cmd convention requires uppercase)
        """Exit on Ctrl-D."""
        print()
        return self.do_quit(line)

    # ------------------------------------------------------------------
    # Help shortcut
    # ------------------------------------------------------------------

    def do_help(self, arg: str) -> None:
        """Show help."""
        super().do_help(arg)


def main() -> None:
    """Start the interactive REPL."""
    logging.basicConfig(format="%(levelname)s %(message)s", level=logging.WARNING)
    try:
        ValidatorREPL().cmdloop()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)


if __name__ == "__main__":
    main()
