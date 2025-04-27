from mcp.client.stdio import stdio_client
from mcp import ClientSession, types
from subprocess import Popen, PIPE
import sys, asyncio, json

async def _call(tool, args):
    proc = Popen([sys.executable, "-m", "src.mcp.forge_server"], stdin=PIPE, stdout=PIPE)
    async with stdio_client(proc) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool(tool, args)
            return res

def test_get_insights():
    out = asyncio.run(_call("get_insights", {"domain":"ai","limit":1}))
    assert isinstance(out, list) 