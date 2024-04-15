import os

import botocore.exceptions

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_resource, get_logger

logger = get_logger(os.path.basename(__file__))


class Group(IResource):

    def __init__(self, arn: str, name: str = None, tags: list = None, region: str = None):
        if not name:
            name = arn.split(':')[-1]
        super().__init__(arn, name, tags, region)

    def remove(self):
        logger.info(f"Trying to delete resource: {self.arn}")
        iam = get_resource('iam', self.region)
        group = iam.Group(self.name)
        group.load()
        try:
            for userName in group.users.all():
                response = group.remove_user(
                    UserName=userName.name
                )
                logger.debug(response)
            response = group.delete()
            logger.debug(response)
            logger.info(f"Resource deleted: {self.arn}")
        except botocore.exceptions.ClientError as e:
            logger.error(f"Cannot delete resource: {self.arn}")
            logger.debug(e)
