from future.utils import raise_from
from typing import Iterable

import ruamel.yaml as yaml
import schema

from ..exceptions import StatechartError
from ..model import Statechart

from .datadict import export_to_dict, import_from_dict

__all__ = ['import_from_yaml', 'export_to_yaml']


class SCHEMA(object):
    contract = {schema.Or('before', 'after', 'always'): schema.Use(str)}

    transition = {
        schema.Optional('target'): schema.Use(str),
        schema.Optional('event'): schema.Use(str),
        schema.Optional('guard'): schema.Use(str),
        schema.Optional('action'): schema.Use(str),
        schema.Optional('contract'): [contract],
        schema.Optional('priority'): schema.Or(schema.Use(int), 'high', 'low'),
    }

    state = dict()  # type: ignore
    state.update({
        'name': schema.Use(str),
        schema.Optional('type'): schema.Or('final', 'shallow history', 'deep history'),
        schema.Optional('on entry'): schema.Use(str),
        schema.Optional('on exit'): schema.Use(str),
        schema.Optional('transitions'): [transition],
        schema.Optional('contract'): [contract],
        schema.Optional('initial'): schema.Use(str),
        schema.Optional('parallel states'): [state],
        schema.Optional('states'): [state],
        schema.Optional('memory'): schema.Use(str)
    })

    statechart = {
        'statechart': {
            'name': schema.Use(str),
            schema.Optional('description'): schema.Use(str),
            schema.Optional('preamble'): schema.Use(str),
            'root state': state,
        }
    }


def import_from_yaml(text=None, filepath=None, *args, **kwargs):
    """
    Import a statechart from a YAML representation (first argument) or a YAML file (filepath argument).

    Unless specified, the structure contained in the YAML is validated against a predefined
    schema (see *sismic.io.SCHEMA*), and the resulting statechart is validated using its *validate()* method.

    kwargs:
        ignore_schema: set to *True* to disable yaml validation.
        ignore_validation: set to *True* to disable statechart validation.


    :param Iterable[str] text: A YAML text. If not provided, filepath argument has to be provided.
    :param str filepath: A path to a YAML file.
    :return: a *Statechart* instance
    :rtype: Statechart
    """
    ignore_schema = kwargs.get("ignore_schema", False)  # type: bool
    ignore_validation = kwargs.get("ignore_validation", False)  # type: bool

    if not text and not filepath:
        raise TypeError('A YAML must be provided, either using first argument or filepath argument.')
    elif text and filepath:
        raise TypeError('Either provide first argument or filepath argument, not both.')
    elif filepath:
        with open(filepath, 'r') as f:
            text = f.read()

    if yaml.version_info < (0, 15):
        data = yaml.safe_load(text)  # type: dict
    else:
        yml = yaml.YAML(typ='safe', pure=True)
        data = yml.load(text)

    if not ignore_schema:
        data = schema.Schema(SCHEMA.statechart).validate(data)

    sc = import_from_dict(data)

    if not ignore_validation:
        sc.validate()
    return sc


def export_to_yaml(statechart, filepath=None):
    """
    Export given *Statechart* instance to YAML. Its YAML representation is returned by this function.
    Automatically save the output to filepath, if provided.

    :param Statechart statechart: statechart to export
    :param str filepath: save output to given filepath, if provided
    :return: A textual YAML representation
    :rtype: str
    """
    output = yaml.dump(export_to_dict(statechart, ordered=False),
                       width=1000, default_flow_style=False)

    if filepath:
        with open(filepath, 'w') as f:
            f.write(output)

    return output