import os

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.factory import get_resources_by_tags, BaseFactory
from aws_swiffer.resources.dynamodb.Table import Table
from aws_swiffer.utils import get_logger, get_base_arn
from aws_swiffer.resources import Bucket

logger = get_logger(os.path.basename(__file__))


class TableFactory(BaseFactory):

    def create_by_tags(self, tags: dict) -> list[IResource]:
        try:
            resource_type_filters = 'dynamodb:table'
            resources = get_resources_by_tags(tags=tags,
                                              resource_type_filters=resource_type_filters,
                                              resource_class=Table)
            return resources
        except Exception as e:
            logger.error(e)
            raise e

    def create_by_arn(self, arn: str) -> IResource:
        name = arn.split('/')[-1]
        arn = f"{get_base_arn('dynamodb')}:table/{name}"
        r = Table(name=name, arn=arn)
        return r

    def create_by_name(self, name: str) -> IResource:
        #arn:aws:dynamodb:eu-west-1:389003593287:table/aes-demo-dynamo-db
        arn = f"{get_base_arn('dynamodb')}:table/{name}"
        r = Table(name=name, arn=arn)
        return r

    def create_by_id(self, resource_id: str) -> IResource:
        return self.create_by_name(resource_id)
