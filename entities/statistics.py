from dataclasses import dataclass

from entities.base_object import Object, log


@dataclass()
class StatRecord:
    name: str
    type_id: int
    color: int
    quantity: int
    obj: Object


cache = {}


class StatRecorder:
    @staticmethod
    def get(obj: Object) -> StatRecord or None:
        type_id = obj.type_id
        type_record = cache.get(type_id, {})
        if not type_record:
            return

        color = obj.color
        color_record = type_record.get(color, None)
        if not color_record:
            return

        return color_record

    @staticmethod
    def recorded(obj):
        return StatRecorder.get(obj) is not None

    @staticmethod
    def record(obj: Object):
        quantity = obj.quantity
        if StatRecorder.recorded(obj):
            recorded_item = StatRecorder.get(obj)
            recorded_item.quantity += quantity
            # log.debug(f"Added record of {quantity} of {obj}")
            return

        # log.debug(f"Recording {obj}")
        name = obj.name_short
        type_id = obj.type_id
        color = obj.color
        if cache.get(type_id, None) is None:
            cache[type_id] = {}

        if cache[type_id].get(color, None) is None:
            stat_obj = StatRecord(name=name, type_id=type_id, color=color, quantity=quantity, obj=obj)
            cache[type_id][color] = stat_obj
        else:
            cache[type_id][color].quantity += quantity
        # log.debug(f"Recording {obj} done")
