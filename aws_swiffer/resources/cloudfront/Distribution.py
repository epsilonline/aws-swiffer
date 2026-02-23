import os
from typing import TYPE_CHECKING

from botocore.exceptions import ClientError

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_client, get_logger

if TYPE_CHECKING:
    from aws_swiffer.utils.context import ExecutionContext

logger = get_logger(os.path.basename(__file__))


class Distribution(IResource):

    def __init__(self, arn: str, name: str = None, tags: list = None, region: str = "us-east-1"):
        """
        name it's id
        """
        if not name:
            name = arn.split('/')[-1]
        self.id = name
        super().__init__(arn, name, tags, region)

    def remove(self, context: 'ExecutionContext' = None):
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Trying to delete resource: {self.arn}")
        client = get_client('cloudfront', self.region)

        etag = self.clean()
        if etag:
            response = client.delete_distribution(
                Id=self.id,
                IfMatch=etag
            )
        else:
            logger.info(f"{prefix}Cannot disable and delte distribution")
        logger.info(f"{prefix}Resource deleted: {self.arn}")
        logger.debug(response)

    def clean(self, context: 'ExecutionContext' = None):
        client = get_client('cloudfront', self.region)
        prefix = context.log_prefix() if context else ""
        etag = None

        try:
            response = client.get_distribution_config(Id=self.id)
            config = response['DistributionConfig']
            etag = response['ETag']

            if not config['Enabled']:
                logger.debug(f"{prefix}Distribution {self.id} is already disabled.")
                return etag

            config['Enabled'] = False

            client.update_distribution(
                Id=self.id,
                DistributionConfig=config,
                IfMatch=etag  # Mandatory for updates
            )

            waiter = client.get_waiter('distribution_deployed')
            waiter.wait(
                Id=self.id,
                WaiterConfig={
                    'Delay': 20,      # Check every 20 seconds (faster than default)
                    'MaxAttempts': 50 # Total attempts before failing
                }
            )

            logger.info(f"{prefix}Successfully disabled distribution: {self.id}")

        except ClientError as e:
            print(f"Error: {e.response['Error']['Message']}")

        return etag