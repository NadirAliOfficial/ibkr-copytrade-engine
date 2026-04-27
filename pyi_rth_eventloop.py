"""PyInstaller runtime hook: ensure an asyncio event loop exists before eventkit imports."""
import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
