import asyncio
from functools import partial


def handle_args(func, args):
    if isinstance(args, (list, tuple)):
        return partial(func, *args)
    elif isinstance(args, dict):
        return partial(func, **args)
    else:
        return partial(func, args)


async def _run_async(loop, func, args_list):
    futures = [
        loop.run_in_executor(
            None,
            handle_args(func, args)
        ) for args in args_list
    ]

    return await asyncio.gather(*futures)


def run_async(func, args_list):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(_run_async(loop, func, args_list))
