import os
from typing import TYPE_CHECKING

import botocore.exceptions

from aws_swiffer.resources.IResource import IResource
from aws_swiffer.utils import get_resource, get_logger, get_client

if TYPE_CHECKING:
    from aws_swiffer.utils.context import ExecutionContext

logger = get_logger(os.path.basename(__file__))


class User(IResource):

    def __init__(self, arn: str, name: str = None, tags: list = None, region: str = None):
        if not name:
            name = arn.split(':')[-1]
        iam = get_resource('iam', self.region)
        self.user = iam.User(self.name)
        self.user.load()
        self.iam_client = get_client('iam', self.region)
        super().__init__(arn, name, tags, region)

    def remove(self, context: 'ExecutionContext' = None):
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Trying to delete resource: {self.arn}")
        
        if not self._should_proceed(context, "delete IAM user"):
            logger.info("Delete skipped")
            return
        
        if context and context.dry_run:
            logger.info(f"{prefix}Would delete IAM user: {self.name}")
            return
        
        try:
            self.delete_all_accesses()
            self.detach_policies()
            self.delete_from_groups()
            response = self.user.delete()
            logger.debug(response)
            logger.info(f"{prefix}Resource deleted: {self.arn}")
        except botocore.exceptions.ClientError as e:
            logger.error(f"Cannot delete resource: {self.arn}")
            logger.debug(e)

    def delete_all_accesses(self):
        self.disable_credentials(True)
        self.disable_ssh_public_keys(True)
        self.disable_codecommit_credentials(True)
        self.delete_mfa_devices()
        self.disable_console_access()

    def disable_credentials(self, delete: bool = False):
        access_keys = self.user.access_keys.all()
        for access_key in access_keys:
            access_key.deactivate()
            if delete:
                access_key.delete()
        logger.info(f"[{self.arn}]: Credentials %s", "deleted" if delete else "disabled")

    def disable_ssh_public_keys(self, delete: bool = False):
        public_keys = self.iam_client.list_ssh_public_keys(UserName=self.name)
        for public_key in public_keys.get("SSHPublicKeys", []):
            self.iam_client.update_ssh_public_key(UserName=self.name,
                                                  SSHPublicKeyId=public_key["SSHPublicKeyId"],
                                                  Status="Inactive")
            if delete:
                self.iam_client.delete_ssh_public_key(UserName=self.name,
                                                      SSHPublicKeyId=public_key["SSHPublicKeyId"])
        logger.debug(f"[{self.arn}]: Public keys %s", "deleted" if delete else "disabled")

    def disable_codecommit_credentials(self, delete: bool = False):
        codecommit_credentials = self.iam_client.list_service_specific_credentials(UserName=self.name,
                                                                                   ServiceName='codecommit.amazonaws'
                                                                                               '.com')
        for codecommit_credential in codecommit_credentials.get("ServiceSpecificCredentials", []):
            self.iam_client.update_service_specific_credential(UserName=self.name, ServiceSpecificCredentialId=
                                                               codecommit_credential["ServiceSpecificCredentialId"],
                                                               Status="Inactive")
            if delete:
                self.iam_client.delete_service_specific_credential(UserName=self.name, ServiceSpecificCredentialId=
                                                                   codecommit_credential["ServiceSpecificCredentialId"])
        logger.info(f"[{self.arn}]: Codecommit credentials %s", "deleted" if delete else "disabled")

    def disable_console_access(self):
        self.user.LoginProfile().delete()
        logger.debug(f"[{self.arn}]: Console access disabled")

    def detach_policies(self):
        for policy in self.user.attached_policies.all():
            logger.debug(f"[{self.arn}] - Remove policy {policy.arn}")
            self.user.detach_policies(PolicyArn=policy.arn)

        for policy in self.user.attached_policies.all():
            logger.debug(f"[{self.arn}] - Remove inline policy {policy.arn}")
            policy.delete()

    def delete_from_groups(self):
        for group in self.user.groups.all():
            logger.debug(f"[{self.arn}] Remove from group {group.group_name}")
            group.remove_user(UserName=self.name)

    def delete_mfa_devices(self):
        # Iterate through the devices and delete them
        for device in self.user.mfa_devices.all():
            device.disassociate()

        logger.debug(f"[{self.arn}]: All MFA devices deleted ")
