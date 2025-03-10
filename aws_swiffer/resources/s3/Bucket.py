import os

import botocore.exceptions

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_resource, get_logger, ask_delete_confirm

logger = get_logger(os.path.basename(__file__))


class Bucket(IResource):

    def __init__(self, arn: str, name: str = None, tags: list = None, region: str = None):
        if not name:
            name = arn.split(':')[-1]
        super().__init__(arn, name, tags, region)
        self.s3 = get_resource('s3', self.region)
        self.bucket = self.s3.Bucket(self.name)

    def remove(self, clear_only: bool = False):
        logger.info(f"Trying to delete resource: {self.arn}")

        delete = ask_delete_confirm(self.name)
        if delete:
            try:
                self.clean()
                try:
                    bucket_website = self.s3.BucketWebsite(self.name)
                    logger.info('Trying to delete website configuration')
                    bucket_website.delete()
                    logger.info('Website configuration deleted')
                except botocore.exceptions.ClientError as e:
                    logger.debug(e)
                response = self.bucket.delete()
                logger.debug(response)
                logger.info(f"Resource deleted: {self.arn}")
            except botocore.exceptions.ClientError as e:
                if e.response.get('Error', {}).get('Code') == 'NoSuchBucket':
                    logger.info("Bucket not found")
                logger.error(f"Cannot delete resource: {self.arn}")
                logger.debug(e)
        else:
            logger.info("Delete skipped")

    def clean(self):
        try:
            logger.info(f'Start clean for: {self.arn}')
            logger.info('Trying to delete old versions')
            self.bucket.object_versions.delete()
            logger.info('Old file versions deleted ')
        except botocore.exceptions.ClientError as e:
            logger.debug(e)
        else:
            logger.info(f"Start delete of all objects in bucket")
            self.bucket.objects.all().delete()
            logger.info(f"Delete of all objects completed")