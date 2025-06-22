ELEMENTS_REGISTRY: dict[str, type] = {}

def register_element(cls_or_name=None, *, cls=None, is_custom=False, category="Прочее"):
    def decorator(actual_cls):
        actual_cls._is_custom = is_custom
        actual_cls.category = category
        ELEMENTS_REGISTRY[actual_cls.__name__] = actual_cls
        return actual_cls

    if isinstance(cls_or_name, type):
        # @register_element
        return decorator(cls_or_name)

    elif isinstance(cls_or_name, str):
        # register_element("name", cls=..., ...)
        if cls is not None:
            cls._is_custom = is_custom
            cls.category = category
            ELEMENTS_REGISTRY[cls_or_name] = cls
            return cls
        else:
            raise ValueError("When using register_element(name, ...), you must provide cls")

    elif cls_or_name is None:
        # @register_element(category="...")
        return decorator

    else:
        raise TypeError("Invalid usage of register_element")

def get_registered_element_names() -> list[str]:
    return list(ELEMENTS_REGISTRY.keys())

def create_element_by_name(name: str):
    cls = ELEMENTS_REGISTRY.get(name)
    if cls:
        return cls()
    return None