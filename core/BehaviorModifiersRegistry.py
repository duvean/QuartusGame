MODIFIERS_REGISTRY = {}  # name -> (modifier_class, editor_class)

def register_modifier(name):
    def decorator(cls):
        MODIFIERS_REGISTRY[name] = {"class": cls, "editor": None}
        return cls
    return decorator

def register_modifier_editor(modifier_class):
    def decorator(editor_cls):
        for entry in MODIFIERS_REGISTRY.values():
            if entry["class"] is modifier_class:
                entry["editor"] = editor_cls
        return editor_cls
    return decorator

def get_available_modifier_names():
    return list(MODIFIERS_REGISTRY.keys())

def create_modifier_by_name(name):
    entry = MODIFIERS_REGISTRY.get(name)
    if entry:
        return entry["class"]()
    return None

def create_modifier_editor(modifier, parent=None):
    for entry in MODIFIERS_REGISTRY.values():
        if isinstance(modifier, entry["class"]) and entry["editor"]:
            return entry["editor"](modifier, parent)
    return None