# Open John — Crypto Market Intelligence for Claude

A Claude Code plugin that turns Claude into a professional crypto market analyst. Pure intelligence, no trading execution — all data from public APIs, no API keys required.

## What You Get

| Tool | Description |
|------|-------------|
| **BTC Market Deep Scan** | Macro environment (DXY, US10Y, SP500, WTI), live news headlines, 4H/1D technicals (RSI, MA, Bollinger), key support/resistance, funding rate, open interest, volume dynamics |
| **Multi-Timeframe Trend Analysis** | 1H → 4H → 1D → 3D resonance analysis with RSI, MACD, EMA alignment, Bollinger width, ATR — outputs trend score from -2 to +2 |
| **Needle-Stick Calculator** | Long/short ratio, funding rate squeeze detection, 50x/100x leverage liquidation prices, stop-loss clusters, ATR extension, psychological levels, FVG gaps |

Supports BTC, ETH, SOL, SUI, and any coin listed on Binance.

## Install

### Claude Code Plugin (recommended)

```bash
/plugin marketplace add sillyleo/open-john
/plugin install crypto-analyzer@open-john
```

Requires [`uv`](https://docs.astral.sh/uv/) — dependencies are handled automatically.

### Claude Code Skill (direct)

```bash
git clone https://github.com/sillyleo/open-john.git
cd open-john
pip install -r crypto-analyzer/requirements.txt
claude --skill ./crypto-analyzer
```

### Claude Desktop (MCP Server)

```bash
git clone https://github.com/sillyleo/open-john.git
cd open-john
pip install -r crypto-analyzer/requirements.txt
```

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "crypto-analyzer": {
      "command": "python3",
      "args": ["/absolute/path/to/open-john/crypto-analyzer/mcp_server.py"]
    }
  }
}
```

Restart Claude Desktop.

## Usage Examples

After installing, just talk to Claude naturally:

- "現在 BTC 盤面怎樣？" → runs BTC market deep scan
- "幫我看一下 ETH 多週期趨勢" → runs multi-timeframe analysis
- "SOL 哪裡可能插針？" → runs needle-stick calculator
- "給我完整的大餅分析" → runs all three tools

## Data Sources

All data comes from free, public APIs — no API keys needed:

- **Binance** — spot & futures market data, klines, funding rate, open interest
- **Yahoo Finance** — macro indicators (DXY, US10Y, SP500, WTI), news headlines

## License

MIT
