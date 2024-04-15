import os

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.factory import get_resources_by_tags, IFactory
from aws_swiffer.utils import get_logger, get_base_arn
from aws_swiffer.resources.iam import User

logger = get_logger(os.path.basename(__file__))


class UserFactory(IFactory):

    def create_by_tags(self, tags: dict) -> list[IResource]:
        try:
            resource_type_filters = 'iam:user'
            resources = get_resources_by_tags(tags=tags,
                                              resource_type_filters=resource_type_filters,
                                              resource_class=User)
            return resources
        except Exception as e:
            logger.error(e)
            raise e

    def create_by_arn(self, arn: str) -> IResource:
        name = arn.split("/")[-1]
        r = User(name=name, arn=arn)
        return r

    def create_by_name(self, name: str) -> IResource:
        arn = f"{get_base_arn('iam', region=self.region)}:user/{name}"
        r = User(name=name, arn=arn)
        return r

    def create_by_id(self, resource_id: str) -> IResource:
        return self.create_by_name(resource_id)
