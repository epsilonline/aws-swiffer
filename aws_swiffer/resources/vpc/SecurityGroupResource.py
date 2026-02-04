"""Security Group Resource class for AWS Swiffer VPC resources."""

import os
from typing import TYPE_CHECKING, Optional, List, Dict

import botocore.exceptions

from aws_swiffer.resources.vpc.VPCResource import VPCResource
from aws_swiffer.utils import get_client, get_logger

if TYPE_CHECKING:
    from aws_swiffer.utils.context import ExecutionContext

logger = get_logger(os.path.basename(__file__))


class SecurityGroupResource(VPCResource):
    """
    Represents a VPC security group resource.
    
    Security groups act as virtual firewalls that control inbound and outbound
    traffic for EC2 instances and other AWS resources.
    """
    
    def __init__(self, arn: str, name: str, vpc_id: str, group_id: str,
                 group_name: str, description: str, tags: list = None, 
                 region: str = None):
        """
        Initialize security group resource.
        
        Args:
            arn: AWS Resource Name
            name: Security group name (from Name tag or group name)
            vpc_id: VPC ID this security group belongs to
            group_id: Security group ID
            group_name: Security group name
            description: Security group description
            tags: Resource tags
            region: AWS region
        """
        super().__init__(
            arn=arn, 
            name=name, 
            vpc_id=vpc_id, 
            resource_type="security-group",
            tags=tags, 
            region=region
        )
        self.group_id = group_id
        self.group_name = group_name
        self.description = description
        self._ec2_client = None
    
    @property
    def ec2_client(self):
        """Lazy-loaded EC2 client."""
        if self._ec2_client is None:
            self._ec2_client = get_client('ec2', self.region)
        return self._ec2_client
    
    def is_default_resource(self) -> bool:
        """
        Check if this is a default security group.
        
        Default security groups are created automatically by AWS for each VPC
        and should be protected from deletion.
        
        Returns:
            True if this is a default security group, False otherwise
        """
        try:
            response = self.ec2_client.describe_security_groups(GroupIds=[self.group_id])
            security_group = response['SecurityGroups'][0]
            is_default = security_group.get('GroupName') == 'default'
            
            if is_default:
                logger.warning(f"Security group {self.group_id} is the default security group and is protected")
            
            return is_default
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error checking if security group {self.group_id} is default: {e}")
            # If we can't determine, err on the side of caution
            return True
    
    def exists(self) -> bool:
        """
        Check if the security group still exists in AWS.
        
        Returns:
            True if security group exists, False otherwise
        """
        try:
            self.ec2_client.describe_security_groups(GroupIds=[self.group_id])
            return True
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidGroupId.NotFound':
                return False
            logger.error(f"Error checking security group existence: {e}")
            return True  # Assume exists if we can't determine
    
    def can_delete(self) -> bool:
        """
        Check if security group can be safely deleted.
        
        Security groups cannot be deleted if:
        - They are default security groups
        - They are referenced by other security groups
        - They are attached to running instances or other resources
        
        Returns:
            True if security group can be deleted, False otherwise
        """
        if not super().can_delete():
            return False
        
        # Check for instances using this security group
        try:
            response = self.ec2_client.describe_instances(
                Filters=[
                    {'Name': 'instance.group-id', 'Values': [self.group_id]},
                    {'Name': 'instance-state-name', 'Values': ['pending', 'running', 'stopping', 'stopped']}
                ]
            )
            
            instances = []
            for reservation in response['Reservations']:
                instances.extend(reservation['Instances'])
            
            if instances:
                logger.warning(f"Security group {self.group_id} is attached to {len(instances)} instances")
                for instance in instances:
                    logger.debug(f"Instance: {instance['InstanceId']} State: {instance['State']['Name']}")
                return False
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error checking instances using security group {self.group_id}: {e}")
            return False
        
        # Check for network interfaces using this security group
        try:
            response = self.ec2_client.describe_network_interfaces(
                Filters=[
                    {'Name': 'group-id', 'Values': [self.group_id]}
                ]
            )
            
            network_interfaces = response['NetworkInterfaces']
            if network_interfaces:
                logger.warning(f"Security group {self.group_id} is attached to {len(network_interfaces)} network interfaces")
                for eni in network_interfaces:
                    logger.debug(f"Network interface: {eni['NetworkInterfaceId']} Status: {eni['Status']}")
                return False
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error checking network interfaces using security group {self.group_id}: {e}")
            return False
        
        # Check for security group references (rules that reference this group)
        if not self._check_security_group_references():
            return False
        
        return True
    
    def _check_security_group_references(self) -> bool:
        """
        Check if other security groups reference this security group in their rules.
        
        Returns:
            True if no references found, False if references exist
        """
        try:
            # Get all security groups in the VPC
            response = self.ec2_client.describe_security_groups(
                Filters=[
                    {'Name': 'vpc-id', 'Values': [self.vpc_id]}
                ]
            )
            
            for sg in response['SecurityGroups']:
                # Skip checking the same security group
                if sg['GroupId'] == self.group_id:
                    continue
                
                # Check inbound rules
                for rule in sg.get('IpPermissions', []):
                    for group_pair in rule.get('UserIdGroupPairs', []):
                        if group_pair.get('GroupId') == self.group_id:
                            logger.warning(f"Security group {self.group_id} is referenced by {sg['GroupId']} in inbound rules")
                            return False
                
                # Check outbound rules
                for rule in sg.get('IpPermissionsEgress', []):
                    for group_pair in rule.get('UserIdGroupPairs', []):
                        if group_pair.get('GroupId') == self.group_id:
                            logger.warning(f"Security group {self.group_id} is referenced by {sg['GroupId']} in outbound rules")
                            return False
            
            return True
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error checking security group references for {self.group_id}: {e}")
            return False
    
    def remove(self, context: 'ExecutionContext' = None) -> None:
        """
        Remove the security group.
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Attempting to delete security group: {self.group_id} ({self.name})")
        
        # Check if we can delete this security group
        if not self.can_delete():
            logger.error(f"Cannot delete security group {self.group_id} - dependencies exist or it's protected")
            return
        
        operation_desc = f"delete security group {self.group_id} ({self.name}) in VPC {self.vpc_id}"
        
        if not self._should_proceed(context, operation_desc):
            logger.info("Security group deletion skipped")
            return
        
        if context and context.dry_run:
            logger.info(f"{prefix}Would delete security group: {self.group_id}")
            return
        
        try:
            self.ec2_client.delete_security_group(GroupId=self.group_id)
            logger.info(f"{prefix}Successfully deleted security group: {self.group_id}")
        
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'InvalidGroupId.NotFound':
                logger.warning(f"{prefix}Security group {self.group_id} not found - may have been deleted already")
            elif error_code == 'DependencyViolation':
                logger.error(f"{prefix}Cannot delete security group {self.group_id} - dependency violation: {error_message}")
            elif error_code == 'InvalidGroup.InUse':
                logger.error(f"{prefix}Cannot delete security group {self.group_id} - group is in use: {error_message}")
            else:
                logger.error(f"{prefix}Failed to delete security group {self.group_id}: {error_code} - {error_message}")
            
            logger.debug(f"Full error details: {e}")
    
    def clean(self, context: 'ExecutionContext' = None) -> None:
        """
        Clean security group dependencies before deletion.
        
        This method handles cleanup of resources that prevent security group deletion:
        - Remove rules that reference other security groups
        - Clear inbound and outbound rules
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Cleaning dependencies for security group: {self.group_id}")
        
        # Clean up security group rules
        self._clean_security_group_rules(context)
    
    def _clean_security_group_rules(self, context: 'ExecutionContext' = None) -> None:
        """
        Clean up security group rules that might prevent deletion.
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        
        try:
            response = self.ec2_client.describe_security_groups(GroupIds=[self.group_id])
            security_group = response['SecurityGroups'][0]
            
            # Clean inbound rules
            inbound_rules = security_group.get('IpPermissions', [])
            if inbound_rules:
                logger.info(f"{prefix}Removing {len(inbound_rules)} inbound rules from security group {self.group_id}")
                
                if context and context.dry_run:
                    logger.info(f"{prefix}Would remove inbound rules from security group: {self.group_id}")
                else:
                    try:
                        self.ec2_client.revoke_security_group_ingress(
                            GroupId=self.group_id,
                            IpPermissions=inbound_rules
                        )
                        logger.info(f"{prefix}Removed inbound rules from security group: {self.group_id}")
                    except botocore.exceptions.ClientError as e:
                        logger.error(f"{prefix}Failed to remove inbound rules from {self.group_id}: {e}")
            
            # Clean outbound rules (except default allow-all rule)
            outbound_rules = security_group.get('IpPermissionsEgress', [])
            custom_outbound_rules = []
            
            for rule in outbound_rules:
                # Skip the default allow-all outbound rule (0.0.0.0/0 on all protocols)
                is_default_rule = (
                    rule.get('IpProtocol') == '-1' and
                    len(rule.get('IpRanges', [])) == 1 and
                    rule['IpRanges'][0].get('CidrIp') == '0.0.0.0/0' and
                    not rule.get('UserIdGroupPairs') and
                    not rule.get('Ipv6Ranges') and
                    not rule.get('PrefixListIds')
                )
                
                if not is_default_rule:
                    custom_outbound_rules.append(rule)
            
            if custom_outbound_rules:
                logger.info(f"{prefix}Removing {len(custom_outbound_rules)} custom outbound rules from security group {self.group_id}")
                
                if context and context.dry_run:
                    logger.info(f"{prefix}Would remove custom outbound rules from security group: {self.group_id}")
                else:
                    try:
                        self.ec2_client.revoke_security_group_egress(
                            GroupId=self.group_id,
                            IpPermissions=custom_outbound_rules
                        )
                        logger.info(f"{prefix}Removed custom outbound rules from security group: {self.group_id}")
                    except botocore.exceptions.ClientError as e:
                        logger.error(f"{prefix}Failed to remove outbound rules from {self.group_id}: {e}")
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"{prefix}Error cleaning security group rules for {self.group_id}: {e}")
    
    def __str__(self) -> str:
        """String representation of the security group resource."""
        return f"SecurityGroup:{self.name}({self.group_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the security group resource."""
        return (f"SecurityGroupResource(group_id={self.group_id}, name={self.name}, "
                f"vpc_id={self.vpc_id}, group_name={self.group_name})")