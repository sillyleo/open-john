#!/usr/bin/env python3
"""
Crypto Analyzer MCP Server
把三個分析腳本包裝成 Claude Desktop 可呼叫的 MCP tools。

使用方式：
  Claude Desktop config 加入：
  {
    "mcpServers": {
      "crypto-analyzer": {
        "command": "python3",
        "args": ["/absolute/path/to/mcp_server.py"]
      }
    }
  }
"""

import asyncio
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

SCRIPTS_DIR = Path(__file__).parent / "scripts"

mcp = FastMCP("crypto-analyzer")


async def _run_script(script_name: str, args: list[str] | None = None) -> str:
    """執行 scripts/ 下的 Python 腳本，回傳 stdout 輸出。"""
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name)]
    if args:
        cmd.extend(args)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        err = stderr.decode().strip()
        return f"[Error] 腳本執行失敗 (exit {proc.returncode}):\n{err}"

    return stdout.decode().strip()


@mcp.tool()
async def btc_market_data() -> str:
    """BTC 市場深度分析：宏觀環境（DXY/US10Y/SP500/WTI）、即時新聞、
    4H/1D 技術指標（RSI、MA、布林通道）、支撐阻力位、資金費率、持倉量、成交量、風險評估。"""
    return await _run_script("btc_market_data.py")


@mcp.tool()
async def mtf_trend_analysis(symbol: str = "BTC/USDT") -> str:
    """多週期共振分析（1H/4H/1D/3D）：RSI、MACD、EMA 排列、布林寬度、ATR，
    輸出 -2 到 +2 趨勢評分與綜合研判。
    symbol 範例：BTC/USDT, ETH/USDT, SOL/USDT"""
    return await _run_script("mtf_trend_master.py", [symbol])


@mcp.tool()
async def needle_stick_analysis(symbol: str = "BTC") -> str:
    """流動性插針與槓桿清算價計算：多空比、資金費率、擠壓信號、
    50x/100x 清算價、止損集群、ATR 延伸、心理關價、FVG 缺口、插針候選位。
    symbol 範例：BTC, ETH, SOL, SUI"""
    return await _run_script("needle_stick_v2.py", [symbol])


if __name__ == "__main__":
    mcp.run(transport="stdio")
