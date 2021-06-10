from abc import ABCMeta, abstractclassmethod
from functools import wraps
import inspect

from typing import Tuple, Dict
from typing import Callable, Awaitable, Iterable
from typing import Optional, Union, Any

from aiohttp import web


AsyncFunc = Handler = Callable[..., Awaitable[web.Response]]
FunctionParams = Dict[str, Tuple[type, Optional[type]]]
JSON = Union[dict, list, str]


def fetch_fn_params(
    fn: Callable
) -> FunctionParams:
    """
    """

    fn_params = {}
    params = inspect.signature(fn).parameters
    for param_name, param in params.items():
        if param_name == 'self':
            continue
        annotation = param.annotation
        default = param.default
        if default is param.empty:
            default = None
        if annotation is param.empty:
            raise ValueError(
                "Parameter {} of function {} has no type hint".format(
                    param_name, fn
                )
            )
        if not issubclass(annotation, (Parameter, web.Request)):
            raise TypeError(
                "{} type hints must be subclass of {}"
                "which {} is not".format(
                    fn.__name__, Parameter, annotation
                )
            )
        fn_params[param.name] = (annotation, default)
    return fn_params


def extraction_wrapper(fn: Handler, classview=False) -> AsyncFunc:
    """
    """

    fn_params = fetch_fn_params(fn)

    @wraps(fn)
    async def wrapped(
        request_or_view: Union[web.Request, web.View]
    ) -> web.Response:
        args = []
        if classview:
            request = request_or_view.request
            args.append(request_or_view)
        else:
            request = request_or_view
        params = {}
        for name, (type, default) in fn_params.items():
            if issubclass(type, web.Request):
                params[name] = request
            params[name] = await type.extract(name, request) or default
        return await fn(*args, **params)

    return wrapped


def extract_classview(cls: web.View) -> web.View:
    """
    """

    for method_name in ('get', 'post', 'put', 'patch', 'delete'):
        handler = getattr(cls, method_name, None)
        if handler is None:
            continue
        patched = with_extraction(handler, classview=True)
        setattr(cls, method_name, patched)
    return cls


def with_extraction(handler=None, classview=False):
    """
    """

    if handler:
        return extraction_wrapper(handler, classview=classview)
    return extraction_wrapper


class ExtractionMeta(ABCMeta):
    """
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        extract_classview(self)


class ParameterMeta(ABCMeta):
    """
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getitem__(cls, key):
        default_attrs = {name: None for name in ('name', 'type')}
        default_attrs.update(cls.__parse_key__(key))
        return type(cls.__name__, (cls, ), default_attrs)


class Parameter(metaclass=ParameterMeta):
    """
    """

    name: Optional[str]
    type: Optional[type]

    def __init__(self, name: str = None, type: type = None) -> None:
        super().__init__()
        self.name = name
        self.type = type

    @abstractclassmethod
    async def extract(name: str, request: web.Request):
        """
        """

    def __parse_key__(key) -> dict:
        params = {}
        if isinstance(key, str):
            params['name'] = key
        elif isinstance(key, type):
            params['type'] = key
        elif isinstance(key, Iterable):
            params.update({k: v for k, v in zip(('name', 'type'), key)})
        return params

    def __repr__(self) -> str:
        return "{}(name: {}, type: {})".format(
            self.__class__.__name__, self.name, self.type
        )


class Header(Parameter):
    """
    """

    @classmethod
    async def extract(cls, name: str, request: web.Request) -> str:
        name = cls.name or name
        return request.headers.get(name)


class Cookie(Parameter):
    """
    """

    @classmethod
    async def extract(cls, name: str, request: web.Request) -> str:
        name = cls.name or name
        return request.cookies.get(name)


class JSONBody(Parameter):
    """
    """

    @classmethod
    async def extract(cls, name: str, request: web.Request) -> JSON:
        return await request.json()


class MatchInfo(Parameter):
    """
    """

    @classmethod
    async def extract(cls, name: str, request: web.Request) -> str:
        name = cls.name or name
        return request.match_info.get(name)


class QueryAttr(Parameter):
    """
    """

    @classmethod
    async def extract(cls, name: str, request: web.Request) -> Any:
        name = cls.name or name
        return request.query.get(name)


class RequestAttr(Parameter):
    """
    """

    name: Optional[str] = None

    @classmethod
    async def extract(cls, name: str, request: web.Request) -> Any:
        name = cls.name or name
        return request.get(name, None)
