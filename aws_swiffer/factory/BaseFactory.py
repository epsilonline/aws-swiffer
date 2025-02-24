from abc import ABC, abstractmethod
from typing import Type
import os
from pathlib import Path

from aws_swiffer.resources.IResource import IResource


class BaseFactory(IFactory):

    def __init__(self):
        self.region = os.getenv('AWS_REGION')

    def create_by_list_file(self, file_path: str) -> list[Type[IResource]]:
        file_path = Path(file_path)
        
        resource_arns: list[Type[IResource]] = []

        with open(file_path) as f:
            resource_name = f.read()
            resource_arn = self.create_by_name(resource_name)
            resource_arns.append(resource_arn)

        return resource_arns