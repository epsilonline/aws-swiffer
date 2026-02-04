import os

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.factory import BaseFactory, get_resources_by_tags
from aws_swiffer.utils import get_logger, get_base_arn
from aws_swiffer.resources.iam import Policy

logger = get_logger(os.path.basename(__file__))


class PolicyFactory(BaseFactory):

    def create_by_tags(self, tags: dict) -> list[IResource]:
        try:
            resource_type_filters = 'iam:policy'
            resources = get_resources_by_tags(tags=tags,
                                            resource_type_filters=resource_type_filters,
                                            resource_class=Policy)
            return resources
        except Exception as e:
            logger.error(e)
            raise e

    def create_by_arn(self, arn: str) -> IResource:
        name = arn.split("/")[-1]
        r = Policy(name=name, arn=arn)
        return r

    def create_by_name(self, name: str) -> IResource:
        arn = f"{get_base_arn('iam', with_region=False)}:policy/{name}"
        r = Policy(name=name, arn=arn)
        return r

    def create_by_id(self, resource_id: str) -> IResource:
        return self.create_by_name(resource_id)
