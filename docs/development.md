# Development Guide

Back links: [Project README](../README.md) | [Docs Index](README.md)

## Testing

Run the full test suite:

```bash
pytest tests/
```

## Contributing

Contributions are welcome. Please include tests for behavior changes and keep docs aligned with the final API.

## Public vs Internal APIs

- Public APIs are exported from `chordelia` and documented in the API docs.
- Names prefixed with `_` are internal implementation details and may change without compatibility guarantees.
- In particular, adapter-registry helpers in `chordelia.sequenceable` are internal; prefer public score conversion entry points such as `Score.from_sequenceable(...)` and `score_from_sequenceable(...)`.

## Versioning

This project uses bump-my-version.

Install:

```bash
uv tool install bump-my-version
```

Preview bump options:

```bash
uv tool run bump-my-version show-bump
```

Bump version:

```bash
uv tool run bump-my-version bump <part>
```

`<part>` can be `major`, `minor`, `patch`, or `pre_l`.

## Publishing to PyPI

Publishing is handled by GitHub Actions when a GitHub Release is published (`.github/workflows/python-publish.yml`).

Typical release flow:

1. Bump the version.
2. Commit and push the bump.
3. Create and publish a GitHub Release.
4. Let CI build and publish the package.

Example release command:

```bash
gh release create v<new_version> --title v<new_version> --generate-notes
```

## Related

- [Installation](installation.md)
- [API Overview](api-overview.md)
