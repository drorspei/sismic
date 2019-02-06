from . import import_from_yaml
from ..model import CompoundState, CompositeStateMixin

__all__ = ['export_to_dot']


def indent(s):
    return '\n'.join('  ' + line for line in s.splitlines())


template_doc = """digraph {{
  compound=true;
  edge [ fontsize={fontsize} ];
  label = <<b>{name}</b>>{nodes}{edges}
}}"""

template_cluster = """
subgraph cluster_{state_name} {{
  style = {style}
  label = "{state_name}"
  node [shape=Mrecord width=.4 height=.4];{inner_nodes}{initial}{additional_points}
}}"""

template_initial = """
  node [shape=point width=.25 height=.25];
  initial_{state_name} -> {initial_state}"""

template_invisible = """
  node [shape=point style=invisible width=0 height=0];
  invisible_{state_name}"""

template_leaf = "\n{state_name} [label=\"{state_name}\" shape=Mrecord]"

template_transition = "\n{source} -> {target} [label=\"{label}\"{ltail}{lhead}{dir}]"


def visit_state(sc, state_name):
    state = sc.state_for(state_name)

    if isinstance(state, CompositeStateMixin):
        if isinstance(state, CompoundState):
            style = "rounded"
            initial = template_initial.format(state_name=state_name, initial_state=state.initial)
        else:
            style = "dashed"
            initial = ""

        # If there are transitions to/from this composite state, we add an invisible point.
        if sc.transitions_to(state_name) or sc.transitions_from(state_name):
            initial = "{}{}".format(initial, template_invisible.format(state_name=state_name))

        inner_nodes = '\n'.join(indent(visit_state(sc, inner)) for inner in sc.children_for(state_name))

        additional_points = '\n'.join(
            "  point_{child}_{ind}".format(child=child, ind=ind)
            for child in sc.children_for(state_name)
            for ind, transition in enumerate(sc.transitions_from(child))
            if transition.target in sc.descendants_for(child))
        if additional_points:
            additional_points = '\n{}\n{}'.format("  node [shape=point margin=0 style=invis width=0. height=0.]",
                                                  additional_points)

        return template_cluster.format(state_name=state_name, initial=initial, inner_nodes=inner_nodes,
                                       style=style, additional_points=additional_points)

    return template_leaf.format(state_name=state_name)


def get_valid_nodes(sc, state_name):
    state = sc.state_for(state_name)

    if isinstance(state, CompositeStateMixin):
        return "invisible_{}".format(state_name), "cluster_{}".format(state_name)

    return state_name, state_name


def get_edge_text(source, target, ltail, lhead, label, dir_):
    if ltail == source:
        ltail = ""
    else:
        ltail = " ltail={}".format(ltail)

    if lhead == target:
        lhead = ""
    else:
        lhead = " lhead={}".format(lhead)

    return template_transition.format(source=source, target=target,
                                      ltail=ltail, lhead=lhead, label=label, dir=dir_)


def get_edges(sc, include_guards, include_actions):
    edges = []
    for state_name in sc.states:
        for ind, transition in enumerate(sc.transitions_from(state_name)):
            valid_source, source = get_valid_nodes(sc, transition.source)
            valid_target, target = get_valid_nodes(sc, transition.target)

            label_parts = []

            if transition.event:
                label_parts.append(transition.event)
            if include_guards and transition.guard:
                label_parts.append('[{}]'.format(transition.guard.replace('"', '\\"')))
            if include_actions and transition.action:
                label_parts.append('/ {}'.format(transition.action.replace('"', '\\"')))

            label = " ".join(label_parts)

            if transition.target in sc.descendants_for(state_name):
                out_point = "point_{}_{}".format(state_name, ind)
                edges.append(get_edge_text(source=valid_source, target=out_point,
                                           ltail=source, lhead=target, label="", dir_=" dir=none"))
                edges.append(get_edge_text(source=out_point, target=valid_target,
                                           ltail=source, lhead=target, label=label, dir_=""))
            else:
                edges.append(get_edge_text(source=valid_source, target=valid_target,
                                           ltail=source, lhead=target, label=label, dir_=""))

    return "".join(edges)


def export_to_dot(sc, include_guards=True, include_actions=True, edge_fontsize=14):
    nodes = indent(visit_state(sc, sc.root))
    edges = indent(get_edges(sc, include_guards, include_actions))

    return template_doc.format(name=sc.name, nodes=nodes, edges=edges, fontsize=edge_fontsize)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str, help="Path to input yaml file.")
    parser.add_argument("output_file", type=str, help="Path to output dot file.")
    parser.add_argument("--no-guards", action="store_false", dest="include_guards",
                        help="Don't show transition guards")
    parser.add_argument("--no-actions", action="store_false", dest="include_actions",
                        help="Don't show tranision actions.")
    parser.add_argument("--trans-font-size", type=int, default=14,
                        help="Set font size of text on transitions. Default: 14.")
    args = parser.parse_args()

    sc = import_from_yaml(filepath=args.input_file)
    dot = export_to_dot(sc=sc, include_guards=args.include_guards, include_actions=args.include_actions,
                        edge_fontsize=args.trans_font_size)
    open(args.output_file, "w").write(dot)


if __name__ == '__main__':
    main()
