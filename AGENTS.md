# Agent Guidelines

Rules for AI agents working on this project.

## Architecture

- Single-file MCP server: `mcp_musicbrainz/server.py` built with [FastMCP](https://gofastmcp.com/)
- Each tool is a function decorated with `@mcp.tool()` and `@cached_tool()`
- `musicbrainzngs` is the sole interface to the MusicBrainz API — [API docs](https://python-musicbrainzngs.readthedocs.io/en/latest/api/)
- Responses are cached to disk (`.musicbrainz_cache/`) with 24h TTL
- Bump `CACHE_VERSION` when changing how API responses are fetched or formatted

## Code Style

- Imports at the top of the file, never inline/local imports
- Run `uv run ruff format .` and `uv run ruff check .` before every commit
- Run `uv run ty check` before every commit for static type checking
- Line length limit: 120 characters
- Use `from __future__ import annotations` (already present)
- Type hints on all function signatures
- Use `uv run` to run all commands — never invoke `python`, `pytest`, `ruff` etc. directly

## Testing

- Tests use mocked `musicbrainzngs` responses, never hit the network
- Mock data in `tests/conftest.py` is derived from real API responses (Reverend Bizarre discography)
- `SEARCH_FUNCS`/`BROWSE_FUNCS` dicts hold references captured at import time — mock via `mock.patch.dict("mcp_musicbrainz.server.SEARCH_FUNCS", ...)`, not `mock.patch("musicbrainzngs.search_*")`
- Other `musicbrainzngs` functions (e.g. `get_artist_by_id`) can be mocked directly
- `conftest.py` provides an autouse `_mock_cache` fixture replacing the disk cache
- Run tests: `uv run pytest tests/ -v`
- Helper functions (e.g. `_fmt_rating`, `_fmt_tags`) are unit-tested in `tests/test_server.py`
- Tool functions are integration-tested in `tests/test_tools.py` with mock API responses
- When adding a field to tool output, add it to the mock data in `conftest.py` and assert it in the corresponding `test_full_output` test
- Verify `musicbrainzngs` function signatures (use `uv run python -c "import inspect, musicbrainzngs; print(inspect.signature(musicbrainzngs.<func>))"`) — parameter names vary between functions (e.g. `includes` not `release_group_includes`)

## Adding a New Tool

1. Add the function in `server.py` with `@mcp.tool()` and `@cached_tool()` decorators
2. Docstring is the tool description seen by the agent — make it precise about ID types
3. Add mock response constant to `tests/conftest.py`
4. Add test class to `tests/test_tools.py` covering happy path and edge cases
5. Update the tools table in `README.md`

## Common Pitfalls

- Release ID ≠ Release Group ID — they are not interchangeable
- `alias-list` and similar lists should use configurable limits, not hardcoded slices
- When truncating output, always tell the agent how to get the rest (which tool, what args)
- `cached_tool` catches `MusicBrainzError`; use `ID_HINT` dict to add guidance for ID mismatches
