import os

import botocore.exceptions

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_resource, get_logger

logger = get_logger(os.path.basename(__file__))


class User(IResource):

    def __init__(self, arn: str, name: str = None, tags: list = None, region: str = None):
        if not name:
            name = arn.split(':')[-1]
        super().__init__(arn, name, tags, region)

    def remove(self):
        logger.info(f"Trying to delete resource: {self.arn}")
        iam = get_resource('iam', self.region)
        user = iam.User(self.name)
        user.load()
        try:
            response = user.delete()
            logger.debug(response)
            logger.info(f"Resource deleted: {self.arn}")
        except botocore.exceptions.ClientError as e:
            logger.error(f"Cannot delete resource: {self.arn}")
            logger.debug(e)
