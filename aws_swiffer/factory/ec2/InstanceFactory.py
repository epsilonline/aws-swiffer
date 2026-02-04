import os

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.factory import get_resources_by_tags, BaseFactory
from aws_swiffer.utils import get_logger, get_base_arn
from aws_swiffer.resources import Instance

logger = get_logger(os.path.basename(__file__))


class InstanceFactory(BaseFactory):

    def create_by_tags(self, tags: dict) -> list[IResource]:
        try:
            resource_type_filters = 'ec2:instance'
            resources = get_resources_by_tags(tags=tags,
                                              resource_type_filters=resource_type_filters,
                                              resource_class=Instance)
            return resources
        except Exception as e:
            logger.error(e)
            raise e

    def create_by_arn(self, arn: str) -> IResource:
        r = Instance(name='', arn=arn)
        return r

    def create_by_name(self, name: str) -> IResource:
        resources = self.create_by_tags({'Name': name})
        if resources:
            return resources[0]
        else:
            raise Exception(f"Instance not found by name: {name}")

    def create_by_id(self, resource_id: str) -> IResource:
        arn = f"{get_base_arn('ec2', self.region)}:instance/{resource_id}"
        r = Instance(name='', arn=arn)
        return r
