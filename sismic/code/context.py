import collections
import copy
from typing import Optional, Union, List, Dict

from ..model import Event, InternalEvent, MetaEvent


__all__ = ['TimeContextProvider', 'EventContextProvider', 'FrozenContext']


class TimeContextProvider(object):
    """
    A context provider for time related predicates. 

    This context exposes time, after, idle, and active.
    Look at their respective documentation for more information.

    This provider needs to be attached to an interpreter.
    """
    def __init__(self):
        self._entry_time = dict()  # type: Dict[str, float]
        self._idle_time = dict()  # type: Dict[str, float]
        self._time = 0  # type: float
        self._configuration = []  # type: List[str]

    @property
    def time(self):
        """
        Current time of the interpreter.
        :rtype: float
        """
        return self._time

    def after(self, name, seconds):
        """
        Return True if and only if given state was entered for more than given
        time, expressed in seconds. 

        :param str name: name of the state.
        :param float seconds: elapsed time to use for comparison.
        :return: True iff. given state was entered for more than given time.
        :rtype: bool
        """
        return self.time - seconds >= self._entry_time[name]

    def idle(self, name, seconds):
        """
        Return True if and only if given state did not fire a transition for more 
        than given time, expressed in seconds. 

        :param str name: name of the state.
        :param float seconds: elapsed time to use for comparison.
        :return: True iff. given state did not fire a transition for more than given time.
        :rtype: bool
        """
        return self.time - seconds >= self._idle_time[name]

    def active(self, name):
        """
        Return True if and only if given state is active.

        :param str name: name of the state.
        :return: True iff. given state is active.
        :rtype: bool
        """
        return name in self._configuration

    def __call__(self, event):
        """

        :param MetaEvent event:
        :return:
        """
        if event.name == 'step started':
            self._time = event.time
        elif event.name == 'state entered':
            self._configuration.append(event.state)
            self._entry_time[event.state] = self._time
            self._idle_time[event.state] = self._time
        elif event.name == 'state exited':
            self._configuration.remove(event.state)
        elif event.name == 'transition processed':
            self._idle_time[event.source] = self._time


class EventContextProvider(object):
    """
    A context provider for event related predicates.
    
    This context exposes send, notify, sent and received.
    Look at their respective documentation for more information.

    The list of events that were sent during the last executed step is 
    available through the ``pending`` attribute. This list should be returned
    by the evaluator on code execution for the events to be effectively sent.

    This provider needs to be attached to an interpreter.
    """
    def __init__(self):
        self.pending = []  # type: List[Event]
        self._sent = []  # type: List[Event]
        self._consumed = None  # type: Optional[Event]

    def send(self, name, **kwargs):
        """
        Create an internal event and store it for further sending.

        :param str name: name of the event.
        :param **kwargs: additional event parameters.
        """
        self.pending.append(InternalEvent(name, **kwargs))

    def notify(self, name, **kwargs):
        """
        Create a meta event and store it for further sending.

        :param str name: name of the event.
        :param **kwargs: additional event parameters.
        """
        self.pending.append(MetaEvent(name, **kwargs))

    def sent(self, name):
        """
        Return True if and only if given internal event was sent during 
        current step.

        :param str name: name of the event.
        :return: True iff. event was sent.
        :rtype: bool
        """
        return any((name == e.name for e in self._sent))

    def received(self, name):
        """
        Return True if and only if given event is currently processed.
        This function should only be used during contract evaluation, and not
        during guard evaluation, as it relies on the *consumed* event.

        :param str name: name of the event.
        :return: True iff. event is processed.
        :rtype: bool
        """
        return getattr(self._consumed, 'name', None) == name
    
    def __call__(self, event):
        """

        :param MetaEvent event:
        :return:
        """
        if event.name == 'event consumed':
            self._consumed = event.event
        elif event.name == 'event sent':
            self._sent.append(event.event)
        elif event.name == 'step started':
            self._consumed = None
            self._sent = []
            self.pending = []
        

class FrozenContext(collections.Mapping):
    """
    A shallow copy of a context. The keys of the underlying context are
    exposed as attributes.
    """
    __slots__ = ['__frozencontext']

    def __init__(self, context):
        """

        :param Dict context:
        """
        self.__frozencontext = {k: copy.copy(v) for k, v in context.items()}

    def __getattr__(self, item):
        try:
            return self.__frozencontext[item]
        except KeyError:
            raise AttributeError('{} has no attribute {}'.format(self, item))

    def __getstate__(self):
        return self.__frozencontext

    def __setstate__(self, state):
        self.__frozencontext = state

    def __getitem__(self, key):
        return self.__frozencontext[key]

    def __len__(self):
        return len(self.__frozencontext)

    def __iter__(self):
        return iter(self.__frozencontext)
