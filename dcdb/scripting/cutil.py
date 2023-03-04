from __future__ import annotations
import typing as t

import ctypes as c
import itertools
import logging
import traceback

import lua
from lua import aux as luaL

import dcdb

if t.TYPE_CHECKING:
    from dcdb.input import StateMachine

logger = logging.getLogger(__name__)


__all__ = ['ScriptError', 'safe_cfunction', 'run_coroutine', 'TypeBuilder']


class ScriptError(Exception):
    pass


def safe_cfunction(f: t.Callable[[c.POINTER(lua.State)], int]) -> lua.CFunction:
    @lua.CFunction
    def safe(state):
        try:
            return f(state)
        except Exception as e:
            msg = '\n'.join(['Python raised exception in lua call', traceback.format_exc()])
            logger.warning('Script error: %s', msg)
            return luaL.error(state, msg.encode('utf-8'))
    return safe


def run_coroutine(state: c.POINTER(lua.State), thread: c.POINTER(lua.State), nargs: int) -> StateMachine:
    logger.debug('Running coroutine %s in state %s (%d arguments)', id(thread), id(state), nargs)
    from dcdb.scripting.proxy.libs import statemachinelib

    status = lua.resume(thread, state, nargs)
    while status == lua.YIELD:
        logging.debug('Yielded to another state machine')
        sm = statemachinelib.check(thread, -1)
        lua.pop(thread, 1)
        yield from sm
        status = lua.resume(thread, state, 0)
    if status != lua.OK:
        err = lua.tostring(thread, -1).decode('utf-8')
        lua.pop(thread, 1)
        raise ScriptError(err)
    lua.pop(state, 1)  # IMPORTANT: Assumes the thread is useless after coroutine and pops it
    logger.debug('Finished coroutine %s successfully', id(thread))


class TypeHandle(c.Structure):

    _fields_ = [('source', c.py_object)]


T = t.TypeVar('T')


class TypeBuilder(t.Generic[T]):

    _indexer: t.Optional[t.Callable[[lua.State], int]]
    _props: t.MutableMapping[bytes, lua.CFunction]
    _setters: t.MutableMapping[bytes, lua.CFunction]
    _methods: t.MutableMapping[bytes, lua.CFunction]
    _index: t.Optional[lua.CFunction]
    _metamethods: t.MutableMapping[bytes, lua.CFunction]

    def __init__(self, name: str) -> None:
        self.name = name.encode('utf-8')
        self._indexer = None
        self._props = {}
        self._setters = {}
        self._methods = {}
        self._index = None
        self._metamethods = {}

        @self.metamethod('__index')
        def index(state):
            logger.debug('Calling __index metamethod of %s metatable', self.name)
            obj = self.check(state, 1)

            if lua.isnumber(state, 2):
                if not self._indexer:
                    return luaL.error(state, f'{obj} does not support numeric indexing'.encode('utf-8'))

                @lua.KFunction
                def continuation(state, status, context):
                    return lua.gettop(state) - 2

                lua.pushcfunction(state, self._indexer)
                lua.pushvalue(state, 1)
                lua.pushvalue(state, 2)
                lua.callk(state, 2, lua.MULTRET, c.cast(None, lua.KContext), continuation)
                return lua.gettop(state) - 2

            key = luaL.checkstring(state, 2)
            luaL.getmetatable(state, self.name)

            if key in self._props:
                lua.pushcfunction(state, self._props[key])
                lua.pushvalue(state, 1)
                lua.call(state, 1, lua.MULTRET)
                return lua.gettop(state) - 3

            if key in self._methods:
                lua.pushcfunction(state, self._methods[key])
                return 1

            msg = f'Cannot access attribute {key.decode("utf-8")} of {obj}'
            return luaL.error(state, msg.encode('utf-8'))

        @self.metamethod('__newindex')
        def set_value(state):
            logger.debug('Calling __newindex metamethod of %s metatable', self.name)
            obj = self.check(state, 1)

            if lua.isnumber(state, 2):
                return luaL.error(state, f'{obj} does not support setting numeric indices'.encode('utf-8'))

            key = luaL.checkstring(state, 2)
            if key in self._setters:
                lua.pushcfunction(state, self._setters[key])
                lua.pushvalue(state, 1)
                lua.pushvalue(state, 3)
                lua.call(state, 2, lua.MULTRET)
                return lua.gettop(state) - 2

            msg = f'Cannot set attribute {key.decode("utf-8")} of {obj}'
            return luaL.error(state, msg.encode('utf-8'))

        @self.metamethod('__tostring')
        def tostring(state):
            logger.debug('Calling __tostring metamethod of %s metatable', self.name)
            obj = self.check(state, 1)
            lua.pushstring(state, repr(obj).encode('utf-8'))
            return 1

        @self.metamethod('__eq')
        def eq(state):
            logger.debug('Calling __eq metamethod of %s metatable', self.name)
            if not self.match(state, 1) or not self.match(state, 2):
                lua.pushboolean(state, False)
                return 1

            obj = self.check(state, 1)
            other = self.check(state, 2)
            lua.pushboolean(state, obj == other)
            return 1

        @self.metamethod('__gc')
        def collect(state):
            logger.debug('Calling __gc metamethod of %s metatable', self.name)
            obj = self.check(state, 1)
            c.pythonapi.Py_DecRef(c.py_object(obj))
            return 0

    def __repr__(self):
        return f'<TypeBuilder {self.name.decode("utf-8")}>'

    def index(self, f: t.Callable[[c.POINTER(lua.State)], int]) -> t.Callable[[c.POINTER(lua.State)], int]:
        self._indexer = safe_cfunction(f)
        return f

    def property(self, name: str) -> t.Callable[[t.Callable[[c.POINTER(lua.State)], int]], t.Callable[[c.POINTER(lua.State)], int]]:
        def wrap(f: t.Callable[[c.POINTER(lua.State)], int]) -> t.Callable[[c.POINTER(lua.State)], int]:
            self._props[name.encode('utf-8')] = safe_cfunction(f)
            return f
        return wrap

    def setter(self, name: str) -> t.Callable[[t.Callable[[c.POINTER(lua.State)], int]], t.Callable[[c.POINTER(lua.State)], int]]:
        def wrap(f: t.Callable[[c.POINTER(lua.State)], int]) -> t.Callable[[c.POINTER(lua.State)], int]:
            self._setters[name.encode('utf-8')] = safe_cfunction(f)
            return f
        return wrap

    def method(self, name: str) -> t.Callable[[t.Callable[[c.POINTER(lua.State)], int]], t.Callable[[c.POINTER(lua.State)], int]]:
        def wrap(f: t.Callable[[c.POINTER(lua.State)], int]) -> t.Callable[[c.POINTER(lua.State)], int]:
            self._methods[name.encode('utf-8')] = safe_cfunction(f)
            return f
        return wrap

    def metamethod(self, name: str) -> t.Callable[[t.Callable[[c.POINTER(lua.State)], int]], t.Callable[[c.POINTER(lua.State)], int]]:
        def wrap(f: t.Callable[[c.POINTER(lua.State)], int]) -> t.Callable[[c.POINTER(lua.State)], int]:
            self._metamethods[name.encode('utf-8')] = safe_cfunction(f)
            return f

        return wrap

    def match(self, state: c.POINTER(lua.State), n: int) -> bool:
        top = lua.gettop(state)
        try:
            if not lua.isuserdata(state, n):
                return False
            if not lua.getmetatable(state, n):
                return False
            lua.getfield(state, -1, b'__name')
            if lua.isstring(state, -1):
                name = lua.tostring(state, -1)
                return name == self.name
            return False
        finally:
            lua.settop(state, top)

    def check(self, state: c.POINTER(lua.State), n: int) -> T:
        logger.debug('Unwrapping Python object from %s metatable', self.name)
        ud_ptr = luaL.checkudata(state, n, self.name)
        pyobj_ptr = c.cast(ud_ptr, c.POINTER(c.py_object))
        obj = pyobj_ptr.contents.value
        logger.debug('Successfully unwrapped object %s', obj)
        return obj

    def build(self, state: c.POINTER(lua.State)) -> None:
        logger.info('Building %s metatable', self.name)

        luaL.newmetatable(state, self.name)
        lib = (luaL.Reg * (len(self._metamethods) + 1))(
            *itertools.starmap(luaL.Reg, self._metamethods.items()),
            luaL.Reg(None, c.cast(None, lua.CFunction))
        )
        luaL.setfuncs(state, lib, 0)
        lua.pop(state, 1)
        logger.debug('Finished building %s metatable', self.name)

    def create(self, state: c.POINTER(lua.State), source: T) -> None:
        ud_ptr = c.cast(lua.newuserdata(state, c.sizeof(c.POINTER(c.py_object))), c.POINTER(c.py_object))
        ud_ptr.contents.value = source
        c.pythonapi.Py_IncRef(ud_ptr.contents)
        luaL.setmetatable(state, self.name)
