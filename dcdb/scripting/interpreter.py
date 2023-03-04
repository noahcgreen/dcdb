from __future__ import annotations
import typing as t

import ctypes as c
import lua
import lua.aux as luaL

from dcdb.event.types import EventType
from dcdb.types import *

from dcdb.scripting.proxy import libs
from dcdb.scripting.cutil import safe_cfunction, ScriptError

if t.TYPE_CHECKING:
    from dcdb.engine import Engine

    Entity = t.Union[Card, Character]


__all__ = ['LuaInterpreter']


class LuaInterpreter:

    engine: Engine
    _state: c.POINTER(lua.State)

    def __init__(self, engine: Engine, seed: int) -> None:
        self.engine = engine
        self.engine.logger.debug('Initializing Lua state')
        self._state = luaL.newstate()
        self.engine.logger.info('Initialized Lua state')
        luaL.openlibs(self._state)
        libs.build_all(self._state)

        self._set_seed(seed)

    def _set_seed(self, seed: int) -> None:
        top = lua.gettop(self._state)

        lua.getglobal(self._state, b'math')

        lua.getfield(self._state, -1, b'randomseed')
        lua.pushnumber(self._state, seed)
        lua.call(self._state, 1, 0)

        lua.pushnil(self._state)
        lua.setfield(self._state, -2, b'randomseed')

        lua.settop(self._state, top)

    @staticmethod
    @safe_cfunction
    def _dctype(state):
        if not lua.isuserdata(state, 1):
            lua.pushnil(state)
        else:
            ud_ptr = lua.touserdata(state, 1)
            pyobj_ptr = c.cast(ud_ptr, c.POINTER(c.py_object))
            type_name = type(pyobj_ptr.contents.value).__name__.encode('utf-8')
            lua.pushstring(state, type_name)
        return 1

    def _push_sandbox(self) -> None:
        lua.newtable(self._state)

        for func in ['print', 'next', 'pairs', 'ipairs', 'pcall']:
            name = func.encode('utf-8')
            lua.getglobal(self._state, name)
            lua.setfield(self._state, -2, name)

        lua.pushcfunction(self._state, self._dctype)
        lua.setfield(self._state, -2, b'dctype')

        for lib in ['table', 'math']:
            name = lib.encode('utf-8')
            lua.getglobal(self._state, name)
            lua.pushvalue(self._state, -1)
            lua.remove(self._state, -2)
            lua.setfield(self._state, -2, name)

        libs.gamelib.create(self._state, self.engine)
        lua.setfield(self._state, -2, b'game')

        libs.card_type_typelib.create(self._state, CardType)
        lua.setfield(self._state, -2, b'Type')

        libs.color_typelib.create(self._state, Color)
        lua.setfield(self._state, -2, b'Color')

        libs.event_type_typelib.create(self._state, EventType)
        lua.setfield(self._state, -2, b'Event')

        libs.region_typelib.create(self._state, Region)
        lua.setfield(self._state, -2, b'Region')

        libs.zone_typelib.create(self._state, Zone)
        lua.setfield(self._state, -2, b'Zone')

        libs.location_typelib.create(self._state, Location)
        lua.setfield(self._state, -2, b'Location')

    def initializer(self, script: str, chunk_name: t.Optional[str] = None) -> t.Callable[[Entity], None]:
        def initialize(entity: Entity) -> None:
            lua.getglobal(self._state, b'load')
            lua.pushstring(self._state, script.encode('utf-8'))
            lua.pushstring(self._state, chunk_name.encode('utf-8'))
            lua.pushstring(self._state, b't')
            self._push_sandbox()

            if isinstance(entity, Card):
                libs.cardlib.create(self._state, entity)
            elif isinstance(entity, Character):
                libs.characterlib.create(self._state, entity)
            else:
                raise TypeError('Entity must be a Card or Character')
            lua.setfield(self._state, -2, b'self')

            lua.call(self._state, 4, lua.MULTRET)
            if not lua.isfunction(self._state, -1):
                err = lua.tostring(self._state, -1).decode('utf-8')
                # Pop nil + error message
                lua.pop(self._state, 2)
                raise ScriptError(err)

            if lua.pcall(self._state, 0, 0, 0) != lua.OK:
                err = lua.tostring(self._state, -1).decode('utf-8')
                lua.pop(self._state, 1)
                raise ScriptError(err)

        return initialize
