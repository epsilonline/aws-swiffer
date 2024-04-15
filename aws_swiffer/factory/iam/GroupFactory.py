import os

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.factory import IFactory
from aws_swiffer.utils import get_logger, get_base_arn
from aws_swiffer.resources.iam import Group

logger = get_logger(os.path.basename(__file__))


class GroupFactory(IFactory):

    def create_by_tags(self, tags: dict) -> list[IResource]:
        # Not supported
        raise Exception("Resource not supported")

    def create_by_arn(self, arn: str) -> IResource:
        name = arn.split("/")[-1]
        r = Group(name=name, arn=arn)
        return r

    def create_by_name(self, name: str) -> IResource:
        arn = f"{get_base_arn('iam', region=self.region)}:group/{name}"
        r = Group(name=name, arn=arn)
        return r

    def create_by_id(self, resource_id: str) -> IResource:
        return self.create_by_name(resource_id)
