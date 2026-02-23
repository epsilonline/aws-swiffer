import os

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.resources.cloudfront.Distribution import Distribution
from aws_swiffer.factory import get_resources_by_tags, BaseFactory
from aws_swiffer.utils import get_logger, get_base_arn, validate_arn

logger = get_logger(os.path.basename(__file__))


class DistributionFactory(BaseFactory):

    def __init__(self):
        self.region = "us-east-1"
        super().__init__()

    def create_by_tags(self, tags: dict) -> list[IResource]:
        try:
            resource_type_filters = 'cloudfront:distribution'
            resources = get_resources_by_tags(tags=tags,
                                            resource_type_filters=resource_type_filters,
                                            resource_class=Distribution, region="us-east-1")
            return resources
        except Exception as e:
            logger.error(e)
            raise e

    def create_by_arn(self, arn: str) -> IResource:
        validate_arn(arn)
        name = arn.split('/')[1]
        return Distribution(name=name, arn=arn)

    def create_by_name(self, name: str) -> IResource:
        arn = f"{get_base_arn('cloudfront', region=self.region)}:distribution/{name}"
        return Distribution(name=name, arn=arn)

    def create_by_id(self, resource_id: str) -> IResource:
        return self.create_by_name(resource_id)
    