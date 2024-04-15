import os

import botocore.exceptions
import botocore.errorfactory

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_client, get_base_arn
from aws_swiffer.utils import get_logger

logger = get_logger(os.path.basename(__file__))


class Service(IResource):

    def __init__(self, arn: str, name: str = None, tags: list = None, region: str = None):
        # arn:aws:ecs:eu-west-1:389003:service/usbim-project-be
        if not arn:
            self.arn = f"{get_base_arn('ecs')}:service/{name}"
        client = get_client('ecs', region)
        for cluster in client.list_clusters()['clusterArns']:
            try:
                services_by_name = client.describe_services(cluster=cluster, services=[arn])['services']
                if services_by_name:
                    self.cluster = services_by_name[0]['clusterArn']
                    break
            except client.exceptions.InvalidParameterException as e:
                logger.debug(e)
                pass
        super().__init__(arn, name, tags, region)

    def remove(self):
        client = get_client('ecs', self.region)
        logger.info(f"Trying to delete resource: {self.arn}")
        try:
            response = client.delete_service(
                cluster=self.cluster,
                service=self.arn
            )
            logger.debug(response)
            logger.info(f"Resource deleted: {self.arn}")
        except botocore.exceptions.ClientError as e:
            logger.error(f"Cannot delete resource: {self.arn}")
            logger.debug(e)
