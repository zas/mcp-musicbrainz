# mcp-musicbrainz

An MCP (Model Context Protocol) server that provides tools for querying the [MusicBrainz](https://musicbrainz.org/) music database. Search for artists, albums, recordings, labels, and more — directly from your AI assistant.

## Tools

| Tool | Description |
|---|---|
| `search_artists` | Search for artists with filters (country, type, gender) |
| `search_releases` | Search for releases with filters (title, artist, label, barcode, catalog number, format) |
| `search_recordings` | Search for recordings with filters (title, artist, release, ISRC) |
| `search_release_groups` | Search for release groups (albums/EPs/singles) with filters (artist, type) |
| `search_labels` | Search for record labels with filters (type, country) |
| `search_works` | Search for musical works/compositions with filters (artist, type) |
| `search_areas` | Search for geographic areas with filters (type) |
| `search_events` | Search for music events with filters (artist, type) |
| `search_instruments` | Search for musical instruments with filters (type) |
| `search_places` | Search for places (venues, studios) with filters (type, area) |
| `search_series` | Search for series (release series, tours) with filters (type) |
| `search_entities_fuzzy` | Typo-tolerant search with automatic exact-first fallback |
| `browse_entities` | Browse entities linked to another entity with paging and optional includes (e.g. all releases by an artist with label info) |
| `get_artist_details` | Artist info with aliases, genres, ratings, URLs, and paged discography |
| `get_release_details` | Release (specific edition) tracklist, barcode, label, and catalog number |
| `get_release_group_details` | Release group (album concept) details with type, genres, and editions (with label, format, country) |
| `get_recording_details` | Recording info with appearances, ISRCs, and genres |
| `get_album_tracks` | Tracklist with durations and performer credits (instruments, vocals) for a release group |
| `get_album_recording_rels` | Recording-level relationships (studios, engineers, producers, works) for all tracks on an album in one call |
| `get_work_details` | Musical work details with composers and lyricists |
| `get_area_details` | Geographic area info (country, city) with aliases |
| `get_label_details` | Label info with type, area, genres, and URLs |
| `get_event_details` | Event info (concert, festival) with date, time, aliases, and tags |
| `get_instrument_details` | Musical instrument info with type, description, aliases, and tags |
| `get_place_details` | Place info (venue, studio) with address, coordinates, aliases, and tags |
| `get_series_details` | Series info (release series, tour) with type, aliases, and tags |
| `get_entity_relationships` | Relationships for any entity type (band members, producers, etc.) |
| `get_cover_art_urls` | Cover art image URLs from the Cover Art Archive |
| `get_release_group_cover_art` | Cover art image URLs for a release group (album concept) |
| `lookup_recording_by_isrc` | Translate a commercial ISRC (Spotify/Apple) to a MusicBrainz recording |
| `lookup_work_by_iswc` | Translate a publisher's ISWC to a MusicBrainz work (composition) |

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/zas/mcp-musicbrainz.git
cd mcp-musicbrainz
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
uv sync
uv run pytest tests/ -v
uv run ruff check .
```

### Pre-commit hooks

Install [pre-commit](https://pre-commit.com/) hooks to automatically run linting and formatting on commit, and tests on push:

```bash
uv run pre-commit install
```

## Caching

Responses are cached locally in `.musicbrainz_cache/` using [diskcache](https://github.com/grantjenks/python-diskcache) with a 24-hour TTL to respect MusicBrainz rate limits.

## License

[GPL-3.0-or-later](LICENSE)
