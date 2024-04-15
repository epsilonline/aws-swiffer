import os

import botocore.exceptions

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_client
from aws_swiffer.utils import get_logger

logger = get_logger(os.path.basename(__file__))


class Ecr(IResource):

    def remove(self):
        client = get_client('ecr', self.region)
        logger.info(f"Trying to delete resource: {self.arn}")
        try:
            response = client.delete_repository(
                repositoryName=self.name,
                force=True
            )
            logger.debug(response)
            logger.info(f"Resource deleted: {self.arn}")
        except botocore.exceptions.ClientError as e:
            logger.error(f"Cannot delete resource: {self.arn}")
            logger.debug(e)

