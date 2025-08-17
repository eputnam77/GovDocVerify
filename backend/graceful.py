import asyncio
import signal
from typing import Any

import uvicorn


async def _serve(server: uvicorn.Server, stop_event: asyncio.Event) -> None:
    """Run the uvicorn server until a stop signal is received."""
    server_task = asyncio.create_task(server.serve())
    await stop_event.wait()
    server.should_exit = True
    await server_task


def run(app: Any, host: str = "0.0.0.0", port: int = 8000) -> None:  # nosec B104
    """Run ``app`` with uvicorn and handle SIGINT/SIGTERM gracefully."""
    config = uvicorn.Config(app, host=host, port=port)
    server = uvicorn.Server(config)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    stop_event = asyncio.Event()

    def _signal_handler(*_: Any) -> None:
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    try:
        loop.run_until_complete(_serve(server, stop_event))
    finally:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.remove_signal_handler(sig)
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
