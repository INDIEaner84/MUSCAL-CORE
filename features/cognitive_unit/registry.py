_registry = {}
_default = None


def register(cognitive_unit):
    _registry[cognitive_unit.agent_type] = cognitive_unit
    global _default
    if cognitive_unit.agent_type == "general" or _default is None:
        _default = cognitive_unit


def resolve(agent_type):
    cu = _registry.get(agent_type)
    if cu is not None:
        return cu
    return _default


def resolve_by_id(unit_id):
    for cu in _registry.values():
        if cu.id == unit_id:
            return cu
    return _default


def default():
    return _default


def all_units():
    return dict(_registry)


def clear():
    _registry.clear()
    global _default
    _default = None
