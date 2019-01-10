from typing import List, Mapping

from .evaluator import Evaluator
from ..model import Event

__all__ = ['DummyEvaluator']


class DummyEvaluator(Evaluator):
    """
    A dummy evaluator that does nothing and evaluates every condition to True.
    """

    def __init__(self, interpreter=None, **kwargs):
        initial_context = kwargs.get("initial_context")
        super(DummyEvaluator, self).__init__(interpreter, initial_context=initial_context)

    @property
    def context(self):
        return dict()

    def _evaluate_code(self, code, **kwargs):
        """

        :param str code:
        :param additional_context:
        :return:
        :rtype: bool
        """
        additional_context = kwargs.get("additional_context")  # type: Mapping
        return True

    def _execute_code(self, code, **kwargs):
        """

        :param str code:
        :param additional_context:
        :return:
        :rtype: List[Event]
        """
        additional_context = kwargs.get("additional_context")  # type: Mapping
        return []
