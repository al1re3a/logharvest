# LogHarvest

**Turn 100,000 noisy log lines into the five failures that matter.**

LogHarvest is a dependency-free Python CLI that detects error events, keeps useful stack context, removes volatile values, and groups repeated failures under stable fingerprints.

```bash
logharvest production.log --top 10
```

## Features

- Understands common log levels and multiline stack traces
- Normalizes UUIDs, IPs, durations, paths, URLs, and changing IDs
- Ranks fatal failures before frequent warnings
- Text, Markdown, and JSON reports
- Stable fingerprints for incident updates and issue deduplication
- Local, streaming-friendly workflow with no log upload

## Examples

```bash
python -m pip install -e .
logharvest examples/service.log
tail -n 100000 app.log | logharvest --format markdown
logharvest app.log --errors-only --format json > summary.json
```

Sample output:

```text
LogHarvest: 3 events -> 2 groups (6 lines)
ERROR    x2     ...  request <n> failed from <ip> after <n>
WARN     x1     ...  cache latency <n>
```

## Philosophy

LogHarvest is intentionally deterministic. It helps an engineer or coding agent choose where to investigate without inventing a root cause or sending production data to a model.

## Development

```bash
python -m unittest discover -s tests -v
```

## License

MIT
