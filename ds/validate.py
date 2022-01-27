from typing import Any, Callable, ParamSpec, Type, TypeVar
from inspect import signature

P = ParamSpec('P')
R = TypeVar('R')

def assert_types(**type_mappings: Type[Any]) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            sig = signature(func).bind(*args, **kwargs)
            sig.apply_defaults()
            params = sig.arguments
            for arg_name, arg_type in type_mappings.items():
                assert isinstance(params[arg_name], arg_type), \
                    f'{arg_name} is not of type {arg_type}'
            return func(*args, **kwargs)
        return wrapper
    return decorator

def _slice_validation_error(index: Any) -> str | None:
    start, stop, step = index.start, index.stop, index.step
    try:
        [][start:stop:step]
        return None
    except (ValueError, TypeError) as exc:
        return str(exc)