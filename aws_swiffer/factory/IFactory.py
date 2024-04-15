from abc import ABC, abstractmethod
from typing import Type
import os

from aws_swiffer.resources.IResource import IResource


class IFactory(ABC):

    def __init__(self):
        self.region = os.getenv('AWS_REGION')

    @abstractmethod
    def create_by_tags(self, tags: dict) -> list[Type[IResource]]:
        raise NotImplementedError

    @abstractmethod
    def create_by_arn(self, arn: str) -> Type[IResource]:
        raise NotImplementedError

    @abstractmethod
    def create_by_name(self, name: str) -> Type[IResource]:
        raise NotImplementedError

    @abstractmethod
    def create_by_id(self, resource_id: str) -> IResource:
        raise NotImplementedError

