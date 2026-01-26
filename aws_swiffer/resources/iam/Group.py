import os
from typing import TYPE_CHECKING

import botocore.exceptions

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_resource, get_logger

if TYPE_CHECKING:
    from aws_swiffer.utils.context import ExecutionContext

logger = get_logger(os.path.basename(__file__))


class Group(IResource):

    def __init__(self, arn: str, name: str = None, tags: list = None, region: str = None):
        if not name:
            name = arn.split(':')[-1]
        super().__init__(arn, name, tags, region)

    def remove(self, context: 'ExecutionContext' = None):
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Trying to delete resource: {self.arn}")
        
        if not self._should_proceed(context, "delete IAM group"):
            logger.info("Delete skipped")
            return
        
        if context and context.dry_run:
            logger.info(f"{prefix}Would delete IAM group: {self.name}")
            return
        
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
            logger.info(f"{prefix}Resource deleted: {self.arn}")
        except botocore.exceptions.ClientError as e:
            logger.error(f"Cannot delete resource: {self.arn}")
            logger.debug(e)
