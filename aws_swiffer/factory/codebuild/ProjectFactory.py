import os

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.resources.codebuild import Project
from aws_swiffer.factory import get_resources_by_tags, IFactory
from aws_swiffer.utils import get_logger, validate_arn, get_base_arn

logger = get_logger(os.path.basename(__file__))


class ProjectFactory(IFactory):

    def create_by_tags(self, tags: dict) -> list[IResource]:
        try:
            resource_type_filters = 'codebuild:project'
            resources = get_resources_by_tags(tags=tags,
                                              resource_type_filters=resource_type_filters,
                                              resource_class=Project)
            return resources
        except Exception as e:
            logger.error(e)
            raise e

    def create_by_arn(self, arn: str) -> IResource:
        validate_arn(arn)
        name = arn.split('/')[-1]
        return Project(arn=arn, name=name)

    def create_by_name(self, name: str) -> IResource:
        arn = f"{get_base_arn('codebuild')}:project/{name}"
        return Project(arn=arn, name=name)

    def create_by_id(self, resource_id: str) -> IResource:
        return self.create_by_name(resource_id)
