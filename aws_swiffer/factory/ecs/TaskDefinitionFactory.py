import os

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.resources.ecs.TaskDefinition import TaskDefinition
from aws_swiffer.factory import get_resources_by_tags, IFactory
from aws_swiffer.utils import get_logger

logger = get_logger(os.path.basename(__file__))


class TaskDefinitionFactory(IFactory):

    def create_by_tags(self, tags: dict) -> list[IResource]:
        try:
            resource_type_filters = 'ecs:task-definition'
            resources = get_resources_by_tags(tags=tags,
                                              resource_type_filters=resource_type_filters,
                                              resource_class=TaskDefinition)
            return resources
        except Exception as e:
            logger.error(e)
            raise e

    def create_by_arn(self, arn: str) -> IResource:
        raise NotImplementedError

    def create_by_name(self, name: str) -> IResource:
        raise NotImplementedError

    def create_by_id(self, resource_id: str) -> IResource:
        return self.create_by_name(resource_id)
