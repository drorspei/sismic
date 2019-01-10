import threading
import time
import warnings

from collections import Counter
from functools import wraps
from typing import Any, Callable, List, Mapping

from .interpreter import Interpreter
from .model import MacroStep

__all__ = ['log_trace', 'run_in_background', 'coverage_from_trace']


def log_trace(interpreter):
    """
    Return a list that will be populated by each value returned by the *execute_once* method
    of given interpreter.

    :param Interpreter interpreter: an *Interpreter* instance
    :return: a list of *MacroStep*
    :rtype: List[MacroStep]
    """
    func = interpreter.execute_once
    trace = []

    @wraps(func)
    def new_func():
        step = func()
        if step:
            trace.append(step)
        return step

    interpreter.execute_once = new_func  # type: ignore
    return trace


def coverage_from_trace(trace):
    """
    Given a list of macro steps considered as the trace of a statechart execution, return *Counter* objects
    that counts the states that were entered, the states that were exited and the transitions that were processed.

    :param List[MacroStep] trace: A list of macro steps
    :return: A dict whose keys are "entered states", "exited states" and "processed transitions" and whose values are Counter object.
    :rtype: Mapping[str, Counter]
    """
    entered_states = []
    exited_states = []
    processed_transitions = []

    for macrostep in trace:
        for microstep in macrostep.steps:
            entered_states.extend(microstep.entered_states)
            exited_states.extend(microstep.exited_states)
            if microstep.transition:
                processed_transitions.append(microstep.transition)

    return {
        'entered states': Counter(entered_states),
        'exited states': Counter(exited_states),
        'processed transitions': Counter(processed_transitions)
    }


def run_in_background(interpreter,
                      delay=0.05,
                      callback=None):
    """
    Run given interpreter in background. The interpreter is ran until it reaches a final configuration.
    You can manually stop the thread using the added *stop* of the returned Thread object.
    This is for convenience only and should be avoided, because a call to *stop* puts the interpreter in
    an empty (and thus final) configuration, without properly leaving the active states.

    :param Interpreter interpreter: an interpreter
    :param float delay: delay between each call to *execute()*
    :param Callable[[List[MacroStep]], Any] callback: a function that accepts the result of *execute*.
    :return: started thread (instance of *threading.Thread*)
    :deprecated: since 1.3.0, use runner.AsyncRunner instead.
    :rtype: threading.Thread
    """
    warnings.warn('Deprecated since 1.3.0. Use runner.AsyncRunner instead.', DeprecationWarning)

    def _task():
        while not interpreter.final:
            steps = interpreter.execute()
            if callback:
                callback(steps)
            time.sleep(delay)
    thread = threading.Thread(target=_task)

    def stop_thread():
        interpreter._configuration = set()

    thread.stop = stop_thread  # type: ignore

    thread.start()
    return thread

