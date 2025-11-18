# Quick Start

1. **Configure Policy**

Run the config wizard:

```bash
oblivion wizard
```

2. **Set API Token**

Export your API token (or use the default):

```bash
export OBLIVION_API_TOKEN=changeme
```

3. **Launch the API and Dashboard**

```bash
oblivion api
```

Visit [http://localhost:8000/dashboard](http://localhost:8000/dashboard?token=changeme)

4. **Emulate an Attack**

From CLI:

```bash
oblivion emulate
```

5. **Try Dry-Run Mode**

```bash
oblivion --dry-run api
```

All actions are simulated only.

6. **Use the Scenario Runner**

```bash
oblivion scenario run docs/scenarios/examples/web_scan.yaml
```