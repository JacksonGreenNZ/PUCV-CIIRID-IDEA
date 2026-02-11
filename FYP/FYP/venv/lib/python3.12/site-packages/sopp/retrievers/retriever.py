from abc import ABC, abstractmethod


class Retriever(ABC):
    @abstractmethod
    def retrieve(self) -> list:
        pass
