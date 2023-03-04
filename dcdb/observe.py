from __future__ import annotations
import typing as t

__all__ = ['Observer', 'Observable', 'ObservableProperty', 'ObservableCollection']


# TODO: Make generic


class Observer:

    pass


class Observable:

    _observers: t.List[Observer]
    _properties: t.Dict[ObservableProperty, t.Any]

    def __init__(self) -> None:
        self._observers = []
        self._properties = {}

    def register(self, observer: Observer) -> None:
        self._observers.append(observer)

    def deregister(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def notify(self, event_type: str, *args: t.Any) -> None:
        f_name = f'observe_{event_type}'
        for observer in reversed(self._observers):
            try:
                observe = getattr(observer, f_name)
            except AttributeError:
                pass
            else:
                observe(self, *args)


T = t.TypeVar('T')


class ObservableProperty(t.Generic[T]):

    name: str

    def __set_name__(self, owner, name) -> None:
        self.name = name

    def __get__(self, instance, owner) -> T:
        if not instance:
            return self
        try:
            return instance._properties[self]
        except KeyError:
            raise AttributeError(f'{instance} has no attribute {self.name}')

    def __set__(self, instance, value) -> None:
        instance._properties[self] = value
        instance.notify(self.name)


U = t.TypeVar('U')


class ObservableCollection(t.MutableSequence[U], Observable):

    def __setitem__(self, key: int, value: U) -> None:
        self.notify('set', key, value)

    def __delitem__(self, key: int) -> None:
        self.notify('delete', key)
        self.notify('length')

    def insert(self, index: int, object: U) -> None:
        self.notify('insert', index, object)
        self.notify('length')
