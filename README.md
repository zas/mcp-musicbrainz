# mcp-musicbrainz

An MCP (Model Context Protocol) server that provides tools for querying the [MusicBrainz](https://musicbrainz.org/) music database. Search for artists, albums, recordings, labels, and more — directly from your AI assistant.

## Tools

| Tool | Description |
|---|---|
| `search_entities` | Search for any MusicBrainz entity (artist, release, recording, label, work, etc.) using Lucene syntax |
| `browse_entities` | Browse entities linked to another entity with paging (e.g. all releases by an artist) |
| `get_artist_details` | Artist info with aliases, genres, ratings, URLs, and full discography |
| `get_release_details` | Release details including tracklist, barcode, label, and catalog number |
| `get_recording_details` | Recording info with appearances, ISRCs, and genres |
| `get_album_tracks` | Tracklist with durations for a release group |
| `get_label_details` | Label info with type, area, and URLs |
| `get_cover_art_urls` | Cover art image URLs from the Cover Art Archive |
| `lookup_by_barcode` | Find a release by UPC/EAN barcode |

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/zas/mcp-musicbrainz.git
cd mcp-musicbrainz
uv venv
uv sync
```

## Usage

### Standalone

```bash
uv run mcp-musicbrainz
```

### Claude Desktop

Add to `claude_desktop_config.json`:

### Kiro CLI

Add to `~/.kiro/settings/mcp.json`:

### Cursor

Add to `.cursor/mcp.json` in your project:

### Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

All use the same configuration:

```json
{
  "mcpServers": {
    "musicbrainz": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-musicbrainz", "mcp-musicbrainz"]
    }
  }
}
```

## Development

```bash
uv sync --all-groups
uv run pytest tests/ -v
uv run ruff check .
```

## Caching

Responses are cached locally in `.musicbrainz_cache/` using [diskcache](https://github.com/grantjenks/python-diskcache) with a 24-hour TTL to respect MusicBrainz rate limits.

## License

[GPL-3.0-or-later](LICENSE)
