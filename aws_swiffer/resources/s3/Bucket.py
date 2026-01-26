import os
from typing import TYPE_CHECKING

import botocore.exceptions

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_resource, get_logger

if TYPE_CHECKING:
    from aws_swiffer.utils.context import ExecutionContext

logger = get_logger(os.path.basename(__file__))


class Bucket(IResource):

    def __init__(self, arn: str, name: str = None, tags: list = None, region: str = None):
        if not name:
            name = arn.split(':')[-1]
        super().__init__(arn, name, tags, region)
        self.s3 = get_resource('s3', self.region)
        self.bucket = self.s3.Bucket(self.name)

    def remove(self, context: 'ExecutionContext' = None):
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Trying to delete resource: {self.arn}")

        if not self._should_proceed(context, "delete bucket"):
            logger.info("Delete skipped")
            return
        
        if context and context.dry_run:
            logger.info(f"{prefix}Would delete bucket: {self.name}")
            return

        try:
            self.clean(context)
            try:
                bucket_website = self.s3.BucketWebsite(self.name)
                logger.info(f'{prefix}Trying to delete website configuration')
                bucket_website.delete()
                logger.info(f'{prefix}Website configuration deleted')
            except botocore.exceptions.ClientError as e:
                logger.debug(e)
            response = self.bucket.delete()
            logger.debug(response)
            logger.info(f"{prefix}Resource deleted: {self.arn}")
        except botocore.exceptions.ClientError as e:
            if e.response.get('Error', {}).get('Code') == 'NoSuchBucket':
                logger.info("Bucket not found")
            logger.error(f"Cannot delete resource: {self.arn}")
            logger.debug(e)

    def clean(self, context: 'ExecutionContext' = None):
        prefix = context.log_prefix() if context else ""
        
        if context and context.dry_run:
            logger.info(f"{prefix}Would clean bucket: {self.name}")
            return
        
        try:
            logger.info(f'{prefix}Start clean for: {self.arn}')
            logger.info(f'{prefix}Trying to delete old versions')
            self.bucket.object_versions.delete()
            logger.info(f'{prefix}Old file versions deleted ')
        except botocore.exceptions.ClientError as e:
            logger.debug(e)
        else:
            logger.info(f"{prefix}Start delete of all objects in bucket")
            self.bucket.objects.all().delete()
            logger.info(f"{prefix}Delete of all objects completed")