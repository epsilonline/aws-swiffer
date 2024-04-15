import os
import re

import botocore.exceptions

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_client
from aws_swiffer.utils import get_logger

logger = get_logger(os.path.basename(__file__))


class TaskDefinition(IResource):

    def __init__(self, arn: str, name: str = None, tags: list = None, region: str = None):
        # arn:aws:ecs:eu-west-1:38993287:task-definition/test:155
        self.task_definition = arn.split('/')[-1]
        self.family = re.sub(r':[0-9]+', '', self.task_definition)
        self.revision = self.task_definition.split(':')[-1]
        super().__init__(arn, name, tags, region)

    def remove(self):
        client = get_client('ecs', self.region)
        logger.info(f"Trying to delete resource: {self.arn}")
        try:
            response = client.deregister_task_definition(
                taskDefinition=self.task_definition
            )
            logger.debug(response)
        except botocore.exceptions.ClientError:
            logger.info(f"Cannot deactivate task, trying to delete")
        try:
            response = client.delete_task_definitions(
                taskDefinitions=[self.task_definition]
            )
            logger.debug(response)
            logger.info(f"Resource deleted: {self.arn}")
        except botocore.exceptions.ClientError as e:
            logger.error(f"Cannot delete resource: {self.arn}")
            logger.debug(e)
