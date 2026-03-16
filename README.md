# Open John — Crypto Market Intelligence for AI Agents

An AI agent skill/plugin that turns your AI into a conservative, data-driven crypto market analyst with day trading strategy support. Pure intelligence, no trading execution — all data from public APIs, no API keys required.

Works with **Claude Code**, **Claude Desktop**, and **OpenClaw**.

## Skills

### Crypto Analyzer (market intelligence)

| Tool | Description |
|------|-------------|
| **BTC Market Deep Scan** | Macro environment (DXY, US10Y, SP500, WTI), live news headlines, 4H/1D technicals (RSI, MA, Bollinger), key support/resistance, funding rate, open interest, volume dynamics |
| **Multi-Timeframe Trend Analysis** | 1H → 4H → 1D → 3D resonance analysis with RSI, MACD, EMA alignment, Bollinger width, ATR — outputs trend score from -2 to +2 |
| **Needle-Stick Calculator** | Long/short ratio, funding rate squeeze detection, 50x/100x leverage liquidation prices, stop-loss clusters, ATR extension, psychological levels, FVG gaps |

Supports BTC, ETH, SOL, SUI, and any coin listed on Binance.

### Day Trading (short-term strategies)

| Strategy | Description |
|----------|-------------|
| **Breakout** | Enter on confirmed breakouts of 4H swing highs/lows with volume confirmation |
| **Retest** | Enter on pullback to broken support/resistance with FVG confluence |
| **Needle Reversal** | Enter on rapid recovery from liquidation zones (50x/100x LP areas) |
| **Trend Following** | Enter on EMA pullbacks in confirmed trends |

Includes position sizing calculator, stop-loss rules, partial take-profit strategies, and a strategy selection decision tree.

## Personality

The analyst is deliberately **conservative and risk-aware**:

- Never gives buy/sell signals — provides intelligence for you to decide
- **3-Minute Rational Review** — forces 4 questions before any trade decision
- **Anti-chase protection** — warns against buying rebounds after crashes
- Labels confidence levels (high/medium/low) on every judgment
- Always includes risk warnings alongside bullish signals
- Stays calm during extreme sentiment (FOMO / FUD)
- Prioritizes macro signals over short-term technicals when they conflict
- Built-in lessons from real trading mistakes

## Install

### Claude Code Plugin (recommended)

```bash
/plugin marketplace add sillyleo/open-john
/plugin install crypto-analyzer@open-john
```

Requires [`uv`](https://docs.astral.sh/uv/) — dependencies are handled automatically.

### OpenClaw

```bash
git clone https://github.com/sillyleo/open-john.git
pip install ccxt pandas pandas-ta requests yfinance

# Copy both skills
cp -r open-john/crypto-analyzer/skills/crypto-analyzer ~/.openclaw/skills/
cp -r open-john/crypto-analyzer/skills/day-trading ~/.openclaw/skills/
```

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

After installing, just talk to your AI naturally:

- "現在 BTC 盤面怎樣？" → runs BTC market deep scan
- "幫我看一下 ETH 多週期趨勢" → runs multi-timeframe analysis
- "SOL 哪裡可能插針？" → runs needle-stick calculator
- "給我完整的大餅分析" → runs all three tools
- "BTC 這裡適合做多嗎？" → triggers day trading analysis with rational review
- "大跌了要不要進場？" → triggers anti-chase protection

## Project Structure

```
open-john/
├── .claude-plugin/
│   └── marketplace.json              ← Claude Code marketplace catalog
├── crypto-analyzer/                  ← Plugin root
│   ├── .claude-plugin/
│   │   └── plugin.json               ← Plugin metadata
│   ├── .mcp.json                     ← Auto-start MCP server (Claude Code)
│   ├── skills/
│   │   ├── crypto-analyzer/
│   │   │   ├── SKILL.md              ← Market intelligence skill
│   │   │   └── scripts/              ← Python analysis scripts
│   │   └── day-trading/
│   │       └── SKILL.md              ← Day trading strategy skill
│   ├── mcp_server.py                 ← MCP server (Claude Desktop)
│   └── requirements.txt
└── README.md
```

## Data Sources

All data comes from free, public APIs — no API keys needed:

- **Binance** — spot & futures market data, klines, funding rate, open interest
- **Yahoo Finance** — macro indicators (DXY, US10Y, SP500, WTI), news headlines

## License

MIT
