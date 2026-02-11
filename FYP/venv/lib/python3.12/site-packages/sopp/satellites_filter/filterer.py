from typing import Callable, List, TypeVar, Any, Optional

T = TypeVar('T')


class Filterer:
    """
    A utility class for applying filters to a list of elements.

    Attributes:
    - _filters (List[Callable[[T], bool]]): List of filter functions to be applied.

    Methods:
    - add_filter(filter_lambda: Callable[[T], bool]) -> Filterer:
        Adds a filter function to the list of filters.

        Parameters:
        - filter_lambda (Callable[[T], bool]): The filter function to be added.

        Returns:
        - Filterer: Returns the Filterer instance for method chaining.

    - apply_filters(elements: List[T]) -> List[T]:
        Applies the stored filters to the provided list of elements.

        Parameters:
        - elements (List[T]): The list of elements to be filtered.

        Returns:
        - List[T]: A new list containing only the elements that pass all applied filters.
    """

    def __init__(self):
        self._filters: List[T] = []

    def add_filter(self, filter_lambda: Callable[[T], bool]):
        if filter_lambda:
            self._filters.append(filter_lambda)
        return self

    def apply_filters(self, elements: List[T]):
        return [element for element in elements if all(f(element) for f in self._filters)]
