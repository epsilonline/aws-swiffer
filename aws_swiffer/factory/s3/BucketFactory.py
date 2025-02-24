import os

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.factory import get_resources_by_tags, BaseFactory
from aws_swiffer.utils import get_logger
from aws_swiffer.resources import Bucket

logger = get_logger(os.path.basename(__file__))


class BucketFactory(BaseFactory):

    def create_by_tags(self, tags: dict) -> list[IResource]:
        try:
            resource_type_filters = 's3:bucket'
            resources = get_resources_by_tags(tags=tags,
                                              resource_type_filters=resource_type_filters,
                                              resource_class=Bucket)
            return resources
        except Exception as e:
            logger.error(e)
            raise e

    def create_by_arn(self, arn: str) -> IResource:
        name = f"arn:aws:s3:::${arn.replace('arn:aws:s3:::', '')}"
        r = Bucket(name=name, arn=arn)
        return r

    def create_by_name(self, name: str) -> IResource:
        arn = f"arn:aws:s3:::{name}"
        r = Bucket(name=name, arn=arn)
        return r

    def create_by_id(self, resource_id: str) -> IResource:
        return self.create_by_name(resource_id)
