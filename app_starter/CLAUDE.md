# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

An MCP (Model Context Protocol) server, built on `FastMCP`, that exposes document-related tools to AI assistants. The server is named `"docs"` and is launched from `main.py`.

## Commands

```bash
# Environment setup
uv venv                 # create the virtual environment
source .venv/bin/activate
uv pip install -e .     # install the package in editable/development mode

# Run the MCP server (stdio transport — exits immediately unless an MCP client is attached to stdin)
uv run main.py

# Tests
uv run pytest                                   # all tests
uv run pytest tests/test_document.py            # single file
uv run pytest tests/test_document.py::TestBinaryDocumentToMarkdown::test_binary_document_to_markdown_with_pdf  # single test
```

## Python version constraint

The project is pinned to **Python 3.13** via `.python-version`, and `pyproject.toml` sets `requires-python = ">=3.10,<3.14"`. This is deliberate: a transitive dependency (`onnxruntime`, pulled in by `markitdown`) has **no wheel for Python 3.14**, so `uv run` fails to sync under 3.14. Do not relax the upper bound unless that dependency ships 3.14 wheels.

## Architecture

Tools follow a two-layer pattern that keeps business logic decoupled from the MCP framework:

- **`tools/`** — each tool is a plain Python function (e.g. `tools/document.py`, `tools/math.py`). These have no MCP dependency, so they are directly unit-testable (see `tests/test_document.py`, which imports and calls the function directly).
- **`main.py`** — the composition root. It creates the `FastMCP("docs")` instance and registers each tool with `mcp.tool()(my_function)`. To expose a new tool, write the function in `tools/`, then register it here.

Tool metadata (description, parameter docs) comes from the function's docstring and pydantic `Field` annotations — the MCP framework surfaces these to the AI assistant, so they are functional, not just documentation.

## Defining MCP tools

(From the README's "Development > Tool Definitions" section.)

Tools are defined as plain Python functions and registered with the MCP server in `main.py`:

```python
mcp.tool()(my_function)
```

**Parameters** — always apply an appropriate type annotation to every function argument (MCP relies on these to build the tool's input schema), and use `Field` from pydantic to describe each one. The descriptions are surfaced to the AI assistant, so they must explain what the parameter does:

```python
from pydantic import Field

def my_tool(
    param1: str = Field(description="Detailed description of this parameter"),
    param2: int = Field(description="Explain what this parameter does")
) -> ReturnType:
    """Comprehensive docstring here"""
    # Implementation
```

**Tool descriptions (docstrings)** should:

- Begin with a one-line summary
- Provide a detailed explanation of functionality
- Explain when to use (and when *not* to use) the tool
- Include usage examples with expected input/output

See `tools/math.py:add` for the reference implementation that follows all of these conventions.

## Tests

Tests live in `tests/`, with binary sample documents in `tests/fixtures/` (`mcp_docs.docx`, `mcp_docs.pdf`). Document-conversion tests read these fixtures as bytes and pass them to the tool function.
