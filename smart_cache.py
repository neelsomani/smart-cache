import ast
from types import ModuleType
from typing import Any, Dict, Callable, Union, Optional
import logging

RESULT_KEY = 'RESULT'
MEMO: Dict[str, Any] = {}
_logger = logging.getLogger(__name__)


def cached_func(func: Callable) -> Any:
    # TODO: Include function arguments in the cache key
    global MEMO
    # TODO: Use unique function identifier rather than name
    if func.__name__ not in MEMO:
        MEMO[func.__name__] = func()
    return MEMO[func.__name__]


class SmartCache:
    """ A class to analyze your code and cache the functional portions """
    def __init__(self, module: ModuleType) -> None:
        self.tree: Optional[ast.Module] = None
        self.n_lines: Optional[int] = None
        self.cache(module.__file__)

    def cache(self, filename: str = 'module.py') -> None:
        """ Generate and save a modified AST """
        # Generate the AST
        with open(filename, 'r') as f:
            example = f.read()
        tree = ast.parse(example)

        # Add internal caching
        SmartCache._modify_ast(tree)

        # Make all functions global so we can eval
        globals_line = ast.Global(
            names=[RESULT_KEY] + [f.name for f in tree.body
                                  if isinstance(f, ast.FunctionDef)],
            lineno=1,
            col_offset=0
        )
        tree.body.insert(0, globals_line)
        self.n_lines = len(example.split('\n'))
        self.tree = tree

    def __getattr__(self, item):
        def func(*args, **kwargs):
            # TODO: Pass args and kwargs
            return self._execute(item)
        return func

    def _execute(self, func_to_evaluate: str) -> Any:
        """ Execute a function against the modified AST """
        assert self.tree is not None and self.n_lines is not None
        original_body = [v for v in self.tree.body]
        # Add a call at the end of the module to execute the function
        self.tree.body.append(
            ast.Assign(
                value=ast.Call(
                    func=ast.Name(
                        id=func_to_evaluate,
                        ctx=ast.Load(),
                        lineno=self.n_lines + 1,
                        col_offset=0
                    ),
                    args=[],
                    keywords=[],
                    lineno=self.n_lines + 1,
                    col_offset=0
                ),
                targets=[ast.Name(
                    id=RESULT_KEY,
                    lineno=self.n_lines + 1,
                    col_offset=0,
                    ctx=ast.Store()
                )],
                lineno=self.n_lines + 1,
                col_offset=0
            )
        )
        exec(compile(self.tree, filename="<ast>", mode="exec"))
        self.tree.body = original_body
        return globals()[RESULT_KEY]

    @classmethod
    def _wrap_call_if_functional(
            cls,
            call: ast.Call,
            func_map: Dict[str, ast.FunctionDef]
    ) -> None:
        """ Wrap the function call with a cache check if it's functional """
        # TODO: Use better function identifier than name
        func_name = call.func.id
        # TODO: Parse the args and identify if all functional
        args, kws = call.args, call.keywords
        if Functional.function(func_map.get(func_name), func_map):
            _logger.debug(f'{func_name} is functional')
            # TODO: Possibly only cache if it takes longer than X seconds
            call.args.append(call.func)
            call.func = ast.Name(
                id='cached_func',
                ctx=ast.Load(),
                lineno=call.func.lineno,
                col_offset=call.func.col_offset
            )
        else:
            # TODO: Recursively cache non-functional methods that are called
            _logger.debug(f'{call.func.id} is not functional')

    @classmethod
    def _modify_ast(cls, tree: ast.Module) -> None:
        """ Modify the AST in-place and insert caching appropriately """
        top_level_funcs = {f.name: f for f in tree.body
                           if isinstance(f, ast.FunctionDef)}
        for func in tree.body:
            for line in func.body:
                if isinstance(line, ast.Expr) or isinstance(line, ast.Assign):
                    if isinstance(line.value, ast.Call):
                        cls._wrap_call_if_functional(
                            line.value,
                            top_level_funcs
                        )
                else:
                    # Unhandled line, treat as non-functional
                    continue


class Functional:
    """ Check if an AST object is functional """
    # TODO: Check that the bound object type is equal for a function call
    pure_fx_set = {'append', 'sum'}

    @classmethod
    def call(cls, call: ast.Call) -> bool:
        """ Identify if the call is to a functional method """
        # TODO: Handle calling a user-defined function
        # TODO: Check that args are functional
        if isinstance(call.func, ast.Attribute):
            if call.func.attr in cls.pure_fx_set:
                return True
        if isinstance(call.func, ast.Name):
            if call.func.id in cls.pure_fx_set:
                return True
        return False

    # TODO: Handle recursive functions
    @classmethod
    def function(
            cls,
            func: Optional[Union[ast.For, ast.FunctionDef]],
            func_map: Dict[str, ast.FunctionDef]
    ) -> bool:
        """ Identify if the method is internally functional """
        if not func:
            return False

        # TODO: Add a decorator @functional for custom caching
        for line in func.body:
            if isinstance(line, ast.Assign):
                if isinstance(line.value, ast.List):
                    continue
                # TODO: Handle other assignment types
                return False
            elif isinstance(line, ast.For):
                # TODO: Check iter function is functional
                if cls.function(line, func_map):
                    continue
                return False
            elif isinstance(line, ast.Expr) or isinstance(line, ast.Return):
                value = line.value
                if isinstance(value, ast.Call):
                    if cls.call(value):
                        continue
                return False

        return True
