from typing import Callable, Any

from ..model import MetaEvent, InternalEvent, Event

from ..exceptions import PropertyStatechartError


__all__ = ['InternalEventListener', 'PropertyStatechartListener']


class InternalEventListener(object):
    """
    Listener that filters and propagates internal events as external events. 
    """
    def __init__(self, callable):
        """

        :param Callable[[Event], Any] callable:
        """
        self._callable = callable

    def __call__(self, event):
        """

        :param MetaEvent event:
        :return:
        """
        if event.name == 'event sent':
            self._callable(Event(event.event.name, **event.event.data))


class PropertyStatechartListener(object):
    """
    Listener that propagates meta-events to given property statechart, executes
    the property statechart, and checks it.
    """
    def __init__(self, interpreter):
        self._interpreter = interpreter

    def __call__(self, event):
        """

        :param MetaEvent event:
        :return:
        """
        self._interpreter.queue(event)
        self._interpreter.execute()
        if self._interpreter.final:
            raise PropertyStatechartError(self._interpreter)