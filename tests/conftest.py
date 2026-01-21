import asyncio
import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def manage_proactor_loop():
    if os.name == 'nt':
        # Force Windows to use ProactorEventLoop for subprocess pipes
        loop = asyncio.WindowsProactorEventLoopPolicy().new_event_loop()
        asyncio.set_event_loop(loop)
        yield loop
        loop.close()
    else:
        yield