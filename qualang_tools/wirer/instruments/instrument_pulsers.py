from dataclasses import dataclass
from typing import Union
from copy import deepcopy


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
    Collection of "stack" Pulser objects.
    Each Pulser entry contains the Controller and FEM Slot on which the thread is running. This wrapper
    can be interacted with as if it were the underlying stack dictionary.
    """

    def __init__(self):
        self.stack = []

    def add(self, pulser: Pulser):
        if not isinstance(pulser, Pulser):
            raise TypeError("Only instances of Pulser can be added to the stack.")
        self.stack.append(pulser)

    def remove(self, pulser: Pulser):
        if not isinstance(pulser, Pulser):
            raise TypeError("Only instances of Pulser can be removed from the stack.")
        try:
            self.stack.remove(pulser)
        except ValueError:
            raise ValueError(f"Pulser {pulser} does not exist in the stack. All the pulsers were used up.")

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
        filtered_pulsers = [pulser for pulser in self.stack if pulser.controller == controller]
        return filtered_pulsers

    def filter_by_slot(self, controller: int, slot: int):
        """
        Returns a list of pulsers that match the given controller.
        """
        filtered_pulsers = [pulser for pulser in self.stack if pulser.controller == controller and pulser.slot == slot]
        return filtered_pulsers

    def filter_unallocated_by_slot(self, controller: int, slot: int):
        """
        Returns a list of pulsers that are not allocated.
        """
        return [pulser for pulser in self.filter_by_slot(controller, slot) if not pulser.allocated]

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
        new_stack = InstrumentPulsers()
        new_stack.stack = [deepcopy(pulser) for pulser in self.stack]
        return new_stack

    def replenish_pulsers(self, controller: int, slot: int = None):
        """
        Replenishes the pulsers for a given controller and slot.
        This is useful when pulsers are allocated and need to be reset.
        """
        if controller is not None and slot is not None:
            for pulser in self.filter_by_slot(controller, slot):
                pulser.allocated = False
        elif controller is not None and slot is None:
            for pulser in self.filter_by_slot(controller, slot):
                pulser.allocated = False
        elif controller is None and slot is None:
            for pulser in self.stack:
                pulser.allocated = False
        else:
            raise ValueError("Must specify either controller, both controller and slot or None.")
