import os

import botocore.exceptions

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_client, get_logger, ask_delete_confirm

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

    def remove(self):
        logger.info(f"Trying to delete resource: {self.arn}")
        ec2 = get_client('ec2', self.region)
        volumes_str = ''
        try:
            instance = ec2.describe_instances(InstanceIds=[self.instance_id])['Reservations'][0]['Instances'][0]
            for volume in instance['BlockDeviceMappings']:
                if volume['Ebs']['DeleteOnTermination']:
                    volume_id = volume['Ebs']['VolumeId']
                    logger.info(f"The volume {volume_id} will delete on instance termination")
                    volumes_str += f"{volume_id} "
            delete = ask_delete_confirm(f"instance {self.instance_id} and volumes: {volumes_str}")
            if delete:
                response = ec2.terminate_instances(InstanceIds=[self.instance_id])
                logger.info(f"Resource deleted: {self.arn}")
                logger.debug(response)
        except botocore.exceptions.ClientError as e:
            logger.error(f"Cannot delete resource: {self.arn}")
            logger.debug(e)


