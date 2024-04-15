import os

import botocore.exceptions
import botocore.errorfactory

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_client
from aws_swiffer.utils import get_logger

logger = get_logger(os.path.basename(__file__))


class Codepipeline(IResource):

    def __init__(self, arn: str, name: str = None, tags: list = None, region: str = None):
        # arn:aws:codepipeline:eu-west-1:389003:usbim-browser-fe-dev
        if not name:
            name = arn.split(':')[-1]
        super().__init__(arn, name, tags, region)

    def remove(self):
        client = get_client('codepipeline', self.region)
        logger.info(f"Trying to delete resource: {self.arn}")
        try:
            response = client.delete_pipeline(
                name=self.name,
            )
            logger.debug(response)
            logger.info(f"Resource deleted: {self.arn}")
        except botocore.exceptions.ClientError as e:
            logger.error(f"Cannot delete resource: {self.arn}")
            logger.debug(e)
