from abc import ABC, abstractmethod

class BaseProvider(ABC):
    @abstractmethod
    def get_response(self, messages, model):
        pass