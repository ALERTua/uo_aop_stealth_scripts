from entities.base_object import Object
from entities.item import Item
from entities.container import Container


def test_object_cache():
    same_id = 'fakeid'
    obj1 = Container.instantiate(same_id)
    obj2 = Container.instantiate(same_id)
    assert obj1 is obj2
    assert len(Object.cache) == 1

    obj3 = Item.instantiate(same_id)
    assert obj1 is not obj3
    assert len(Object.cache) == 1


if __name__ == '__main__':
    test_object_cache()
