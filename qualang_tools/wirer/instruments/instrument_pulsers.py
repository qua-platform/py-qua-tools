from dataclasses import dataclass
from typing import Union

from qualang_tools.wirer.instruments.constants import NUM_THREADS_PER_FEM


@dataclass(eq=False, frozen=False)
class Pulser:
    controller: int
    slot: Union[None, int] = None
    allocated = False

    def __eq__(self, other):
        if not isinstance(other, Pulser):
            return NotImplemented
        return self.controller == other.controller and self.slot == other.slot

    def allocate(self) -> bool:
        if self.allocated:
            return False
        self.allocated = True
        return True


class InstrumentPulsers:
    """
    Collection of "stack" data-structures organized by controller and port.
    Each entry contains the Controller and FEM Slot, the thread is based on. This wrapper
    can be interacted with as if it were the underlying stack dictionary.
    """
    def __init__(self):
        self.stack = []

    def add(self, pulser: Pulser):
        if not isinstance(pulser, Pulser):
            raise TypeError("Only instances of Pulser can be added to the stack.")
        # check if there is already a pulser with the same con, slot, and number
        if len(self.filter_by_slot(pulser.controller, pulser.slot)) > NUM_THREADS_PER_FEM:
            raise ResourceWarning(f"Reached maximum number of pulsers for controller {pulser.controller} and slot {pulser.slot}. Will not add {pulser}.")
        self.stack.append(pulser)

    def remove(self, pulser: Pulser):
        if not isinstance(pulser, Pulser):
            raise TypeError("Only instances of Pulser can be removed from the stack.")
        try:
            self.stack.remove(pulser)
        except ValueError:
            raise ValueError(f"Pulser {pulser} does not exist in the stack.")

    def remove_by_slot(self, controller: int, slot: int):
        """
        Removes the first pulser that match the given controller and slot.
        """
        for pulser in self.stack:
            if pulser.controller == controller and pulser.slot == slot:
                self.stack.remove(pulser)
                return
        raise ValueError(f"No pulser found with controller {controller} and slot {slot}.")

    def filter_by_controller(self, controller: int):
        """
        Returns a list of pulsers that match the given controller.
        """
        return [pulser for pulser in self.stack if pulser.controller == controller]

    def filter_by_slot(self, controller:int, slot: int):
        """
        Returns a list of pulsers that match the given controller.
        """
        return [pulser for pulser in self.stack if pulser.controller == controller and pulser.slot == slot]

    def filter_unallocated_by_slot(self, controller:int, slot: int):
        """
        Returns a list of pulsers that are not allocated.
        """
        return [pulser for pulser in self.stack if pulser.controller == controller and pulser.slot == slot and not pulser.allocated]

    def __iter__(self):
        return iter(self.stack)

    def __getitem__(self, index):
        if isinstance(index, tuple) and len(index) == 2:
            controller, slot = index
            # find the first pulser that matches the controller and slot
            for pulser in self.stack:
                if pulser.controller == controller and pulser.slot == slot:
                    return pulser
        elif isinstance(index, int):
            return self.stack[index]

    def deepcopy(self):
        from copy import deepcopy
        new_stack = InstrumentPulsers()
        new_stack.stack = [deepcopy(pulser) for pulser in self.stack]
        return new_stack
