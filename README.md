# mcp-launchpad-support

MCP server for token launch support retainer - liquidity monitoring, whale tracking, sentiment analysis.

## Tools

### monitor_liquidity_pool
Monitor liquidity pool status for a token launch.

**Parameters:**
- `launch_id` (string, required): Launch identifier
- `pool_address` (string, required): Liquidity pool contract address
- `metrics` (array, optional): Metrics to fetch - tvl, volume_24h, apr, price_impact, concentration (default: all)

### track_whale_wallets
Track whale wallet activity for a token launch.

**Parameters:**
- `launch_id` (string, required): Launch identifier
- `wallets` (array, required): Wallet addresses to track
- `alert_threshold` (number, optional): Alert threshold in USD (default: 10000)

### analyze_sentiment
Analyze market sentiment for a token launch.

**Parameters:**
- `launch_id` (string, required): Launch identifier
- `sources` (array, optional): Data sources - twitter, discord, telegram, news, onchain (default: all)
- `time_window` (string, optional): Time window - 1h, 6h, 24h, 7d (default: 24h)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Connecting to Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "launchpad-support": {
      "command": "python",
      "args": ["/path/to/mcp-launchpad-support/main.py"],
      "cwd": "/path/to/mcp-launchpad-support"
    }
  }
}
```

## License

MIT