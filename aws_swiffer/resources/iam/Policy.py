import os
from typing import TYPE_CHECKING

import botocore.exceptions

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_resource, get_logger

if TYPE_CHECKING:
    from aws_swiffer.utils.context import ExecutionContext

logger = get_logger(os.path.basename(__file__))


class Policy(IResource):

    def __init__(self, arn: str, name: str = None, tags: list = None, region: str = None):
        # arn:aws:iam::3893287:policy/service-role/CodeBuildBasePolicy-usbim-bcf-dev-eu-west-1
        if not name:
            name = arn.split('/')[-1]
        super().__init__(arn, name, tags, region)

    def remove(self, context: 'ExecutionContext' = None):
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Trying to delete resource: {self.arn}")
        
        if not self._should_proceed(context, "delete IAM policy"):
            logger.info("Delete skipped")
            return
        
        if context and context.dry_run:
            logger.info(f"{prefix}Would delete IAM policy: {self.name}")
            return
        
        iam = get_resource('iam', self.region)
        policy = iam.Policy(self.arn)
        try:
            logger.info(f"{prefix}Detach policy from roles")
            for role in policy.attached_roles.all():
                policy.detach_role(RoleName=role)

            logger.info(f"{prefix}Detach policy from users")
            for user in policy.attached_users.all():
                policy.detach_user(UserName=user)

            logger.info(f"{prefix}Detach policy from groups")
            for group in policy.attached_groups.all():
                policy.detach_group(GroupName=group)

            logger.info(f"{prefix}Delete old versions")
            for policy_version in policy.versions.all():
                if not policy_version.is_default_version:
                    policy_version.delete()

            response = policy.delete()
            logger.debug(response)
            logger.info(f"{prefix}Resource deleted: {self.arn}")
        except botocore.exceptions.ClientError as e:
            logger.error(f"Cannot delete resource: {self.arn}")
            logger.debug(e)
