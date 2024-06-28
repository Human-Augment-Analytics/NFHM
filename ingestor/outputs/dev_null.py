from logging import getLogger
from typing import Any

logger = getLogger('outputs.dev_null')

async def dev_null(*_arg) -> list[dict[Any, Any]]:
    print('>> output sent to dev/null')
    # Do nothing