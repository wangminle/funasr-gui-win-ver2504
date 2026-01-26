"""WebSocket 兼容层工具

本模块用于屏蔽不同版本 `websockets` 库在连接参数上的差异，避免运行时因参数不兼容导致崩溃。

目前重点处理：
1. `proxy` 参数：新版本 `websockets.connect` 支持 `proxy`，旧版本可能不支持。
   我们希望“尽可能禁用代理”，以避免环境代理导致连接异常；但若版本不支持则自动降级不传该参数。

说明：
- 该模块仅提供轻量封装，不引入额外依赖。
- 代码使用中文注释，符合项目约定。
"""

from __future__ import annotations

from typing import Any


def connect_websocket(uri: str, disable_proxy: bool = True, **kwargs: Any) -> Any:
    """创建兼容版 WebSocket 连接对象（返回 websockets.connect(...) 的结果）。

    用法示例：
        async with connect_websocket("wss://127.0.0.1:10095", ssl=ctx) as ws:
            ...

    Args:
        uri: WebSocket URI
        disable_proxy: 是否尽可能禁用代理（默认 True）
        **kwargs: 透传给 `websockets.connect` 的其他参数

    Returns:
        `websockets.connect(...)` 返回的连接对象（可 await / 可 async with）
    """
    import inspect
    from contextlib import asynccontextmanager

    import websockets

    def _wrap_if_needed(connect_obj: Any) -> Any:
        """将“仅 awaitable 但不可 async with”的对象包装成异步上下文管理器。

        说明：
        - 正常情况下 `websockets.connect(...)` 返回对象本身就支持 `async with`；
        - 但在单元测试使用 `AsyncMock` 伪造 connect 时，可能返回 coroutine，
          这会导致 `async with` 直接报错且产生“未 await”的警告。
        """
        if hasattr(connect_obj, "__aenter__") and hasattr(connect_obj, "__aexit__"):
            return connect_obj

        if inspect.isawaitable(connect_obj):

            @asynccontextmanager
            async def _ctx() -> Any:
                ws = await connect_obj
                try:
                    yield ws
                finally:
                    close_func = getattr(ws, "close", None)
                    if callable(close_func):
                        maybe = close_func()
                        if inspect.isawaitable(maybe):
                            await maybe

            return _ctx()

        return connect_obj

    if not disable_proxy:
        return _wrap_if_needed(websockets.connect(uri, **kwargs))

    # 尽可能禁用代理，但要兼容旧版本 websockets 不支持 proxy 参数的情况
    connect_kwargs = dict(kwargs)
    connect_kwargs.setdefault("proxy", None)

    try:
        return _wrap_if_needed(websockets.connect(uri, **connect_kwargs))
    except TypeError as e:
        # 旧版本可能报：connect() got an unexpected keyword argument 'proxy'
        if "proxy" in str(e):
            connect_kwargs.pop("proxy", None)
            return _wrap_if_needed(websockets.connect(uri, **connect_kwargs))
        raise
