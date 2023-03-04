import lua
import lua.aux as luaL

from .libs import *


@funclib.metamethod('__call')
def func_call(state):
    func = funclib.check(state, 1)
    lua.pushcfunction(state, func)
    lua.insert(state, 2)
    lua.call(state, lua.gettop(state) - 2, lua.MULTRET)
    return lua.gettop(state) - 1
