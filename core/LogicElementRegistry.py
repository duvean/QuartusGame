ELEMENTS_REGISTRY: dict[str, type] = {}

def register_element(cls_or_name: type | str, cls: type = None):
    if isinstance(cls_or_name, str):
        # Регистрируем по имени (используется для кастомных)
        if cls:
            ELEMENTS_REGISTRY[cls_or_name] = cls
        return cls
    else:
        # Декоратор для обычных элементов
        cls = cls_or_name
        ELEMENTS_REGISTRY[cls.__name__] = cls
        return cls

def get_registered_element_names() -> list[str]:
    return list(ELEMENTS_REGISTRY.keys())

def create_element_by_name(name: str):
    cls = ELEMENTS_REGISTRY.get(name)
    if cls:
        return cls()
    return None