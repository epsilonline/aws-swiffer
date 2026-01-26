import os
from typing import TYPE_CHECKING

import botocore.exceptions

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_client, get_logger

if TYPE_CHECKING:
    from aws_swiffer.utils.context import ExecutionContext

logger = get_logger(os.path.basename(__file__))


class Instance(IResource):
    # arn:aws:ec2:{Region}:{Account}:instance/{InstanceId}
    def __init__(self, arn: str, name: str, tags: list = None, region: str = None):
        if not name:
            ec2 = get_client('ec2')
            if arn:
                self.instance_id = arn.split("/")[1]
                instance = ec2.describe_instances(InstanceIds=[self.instance_id])['Reservations'][0]['Instances'][0]
                tags = instance['Tags']
                name_list = list(filter(lambda x: x['Key'].lower() == 'name', instance['Tags']))
                self.name = name_list[0] if name_list else None
            else:
                raise Exception('ARN is required')
        region = region or arn.split(':')[3]
        super().__init__(arn=arn, name=arn, tags=tags, region=region)

    def __str__(self):
        return f'{self.arn}'

    def remove(self, context: 'ExecutionContext' = None):
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Trying to delete resource: {self.arn}")
        ec2 = get_client('ec2', self.region)
        volumes_str = ''
        try:
            instance = ec2.describe_instances(InstanceIds=[self.instance_id])['Reservations'][0]['Instances'][0]
            for volume in instance['BlockDeviceMappings']:
                if volume['Ebs']['DeleteOnTermination']:
                    volume_id = volume['Ebs']['VolumeId']
                    logger.info(f"{prefix}The volume {volume_id} will delete on instance termination")
                    volumes_str += f"{volume_id} "
            
            operation_desc = f"terminate instance {self.instance_id}"
            if volumes_str:
                operation_desc += f" and volumes: {volumes_str}"
            
            if not self._should_proceed(context, operation_desc):
                logger.info("Termination skipped")
                return
            
            if context and context.dry_run:
                logger.info(f"{prefix}Would terminate instance: {self.instance_id}")
                return
            
            response = ec2.terminate_instances(InstanceIds=[self.instance_id])
            logger.info(f"{prefix}Resource deleted: {self.arn}")
            logger.debug(response)
        except botocore.exceptions.ClientError as e:
            logger.error(f"Cannot delete resource: {self.arn}")
            logger.debug(e)


