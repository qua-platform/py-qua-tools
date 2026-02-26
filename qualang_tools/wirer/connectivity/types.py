from typing import Union, List, Tuple

ElementType = Union[int, str]
QubitType = Union[int, str]
QubitPairType = Union[Tuple[int, int], Tuple[str, str], Tuple[int, str]]

ElementsType = Union[ElementType, List[ElementType]]
QubitsType = Union[QubitType, List[QubitType]]
QubitPairsType = Union[QubitPairType, List[QubitPairType]]
