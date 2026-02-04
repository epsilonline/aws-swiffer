"""Subnet Resource class for AWS Swiffer VPC resources."""

import os
from typing import TYPE_CHECKING, Optional

import botocore.exceptions

from aws_swiffer.resources.vpc.VPCResource import VPCResource
from aws_swiffer.utils import get_client, get_logger

if TYPE_CHECKING:
    from aws_swiffer.utils.context import ExecutionContext

logger = get_logger(os.path.basename(__file__))


class SubnetResource(VPCResource):
    """
    Represents a VPC subnet resource.
    
    Subnets are fundamental VPC components that provide network isolation
    and IP address allocation within availability zones.
    """
    
    def __init__(self, arn: str, name: str, vpc_id: str, subnet_id: str,
                 availability_zone: str, cidr_block: str, tags: list = None, 
                 region: str = None):
        """
        Initialize subnet resource.
        
        Args:
            arn: AWS Resource Name
            name: Subnet name (from Name tag or subnet ID)
            vpc_id: VPC ID this subnet belongs to
            subnet_id: Subnet ID
            availability_zone: Availability zone
            cidr_block: CIDR block of the subnet
            tags: Resource tags
            region: AWS region
        """
        super().__init__(
            arn=arn, 
            name=name, 
            vpc_id=vpc_id, 
            resource_type="subnet",
            tags=tags, 
            region=region
        )
        self.subnet_id = subnet_id
        self.availability_zone = availability_zone
        self.cidr_block = cidr_block
        self._ec2_client = None
    
    @property
    def ec2_client(self):
        """Lazy-loaded EC2 client."""
        if self._ec2_client is None:
            self._ec2_client = get_client('ec2', self.region)
        return self._ec2_client
    
    def is_default_resource(self) -> bool:
        """
        Check if this is a default subnet.
        
        Default subnets are created automatically by AWS in default VPCs
        and should be protected from deletion.
        
        Returns:
            True if this is a default subnet, False otherwise
        """
        try:
            response = self.ec2_client.describe_subnets(SubnetIds=[self.subnet_id])
            subnet = response['Subnets'][0]
            is_default = subnet.get('DefaultForAz', False)
            
            if is_default:
                logger.warning(f"Subnet {self.subnet_id} is a default subnet and is protected")
            
            return is_default
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error checking if subnet {self.subnet_id} is default: {e}")
            # If we can't determine, err on the side of caution
            return True
    
    def exists(self) -> bool:
        """
        Check if the subnet still exists in AWS.
        
        Returns:
            True if subnet exists, False otherwise
        """
        try:
            self.ec2_client.describe_subnets(SubnetIds=[self.subnet_id])
            return True
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidSubnetID.NotFound':
                return False
            logger.error(f"Error checking subnet existence: {e}")
            return True  # Assume exists if we can't determine
    
    def can_delete(self) -> bool:
        """
        Check if subnet can be safely deleted.
        
        Subnets cannot be deleted if:
        - They are default subnets
        - They have dependencies (network interfaces, instances, etc.)
        - They have running resources
        
        Returns:
            True if subnet can be deleted, False otherwise
        """
        if not super().can_delete():
            return False
        
        # Check for network interfaces in the subnet
        try:
            response = self.ec2_client.describe_network_interfaces(
                Filters=[
                    {'Name': 'subnet-id', 'Values': [self.subnet_id]}
                ]
            )
            
            network_interfaces = response['NetworkInterfaces']
            if network_interfaces:
                logger.warning(f"Subnet {self.subnet_id} has {len(network_interfaces)} network interfaces")
                for eni in network_interfaces:
                    logger.debug(f"Network interface: {eni['NetworkInterfaceId']} "
                               f"Status: {eni['Status']} Type: {eni.get('InterfaceType', 'interface')}")
                return False
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error checking network interfaces in subnet {self.subnet_id}: {e}")
            return False
        
        # Check for instances in the subnet
        try:
            response = self.ec2_client.describe_instances(
                Filters=[
                    {'Name': 'subnet-id', 'Values': [self.subnet_id]},
                    {'Name': 'instance-state-name', 'Values': ['pending', 'running', 'stopping', 'stopped']}
                ]
            )
            
            instances = []
            for reservation in response['Reservations']:
                instances.extend(reservation['Instances'])
            
            if instances:
                logger.warning(f"Subnet {self.subnet_id} has {len(instances)} instances")
                for instance in instances:
                    logger.debug(f"Instance: {instance['InstanceId']} State: {instance['State']['Name']}")
                return False
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error checking instances in subnet {self.subnet_id}: {e}")
            return False
        
        return True
    
    def remove(self, context: 'ExecutionContext' = None) -> None:
        """
        Remove the subnet.
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Attempting to delete subnet: {self.subnet_id} ({self.name})")
        
        # Check if we can delete this subnet
        if not self.can_delete():
            logger.error(f"Cannot delete subnet {self.subnet_id} - dependencies exist or it's protected")
            return
        
        operation_desc = f"delete subnet {self.subnet_id} ({self.name}) in VPC {self.vpc_id}"
        
        if not self._should_proceed(context, operation_desc):
            logger.info("Subnet deletion skipped")
            return
        
        if context and context.dry_run:
            logger.info(f"{prefix}Would delete subnet: {self.subnet_id}")
            return
        
        try:
            self.ec2_client.delete_subnet(SubnetId=self.subnet_id)
            logger.info(f"{prefix}Successfully deleted subnet: {self.subnet_id}")
        
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'InvalidSubnetID.NotFound':
                logger.warning(f"{prefix}Subnet {self.subnet_id} not found - may have been deleted already")
            elif error_code == 'DependencyViolation':
                logger.error(f"{prefix}Cannot delete subnet {self.subnet_id} - dependency violation: {error_message}")
            elif error_code == 'InvalidSubnet.InUse':
                logger.error(f"{prefix}Cannot delete subnet {self.subnet_id} - subnet is in use: {error_message}")
            else:
                logger.error(f"{prefix}Failed to delete subnet {self.subnet_id}: {error_code} - {error_message}")
            
            logger.debug(f"Full error details: {e}")
    
    def clean(self, context: 'ExecutionContext' = None) -> None:
        """
        Clean subnet dependencies before deletion.
        
        This method handles cleanup of resources that prevent subnet deletion:
        - Network interfaces (except those managed by AWS services)
        - Route table associations (custom route tables only)
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Cleaning dependencies for subnet: {self.subnet_id}")
        
        # Clean up network interfaces
        self._clean_network_interfaces(context)
        
        # Clean up custom route table associations
        self._clean_route_table_associations(context)
    
    def _clean_network_interfaces(self, context: 'ExecutionContext' = None) -> None:
        """
        Clean up network interfaces in the subnet.
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        
        try:
            response = self.ec2_client.describe_network_interfaces(
                Filters=[
                    {'Name': 'subnet-id', 'Values': [self.subnet_id]}
                ]
            )
            
            for eni in response['NetworkInterfaces']:
                eni_id = eni['NetworkInterfaceId']
                eni_type = eni.get('InterfaceType', 'interface')
                status = eni['Status']
                
                # Skip AWS-managed network interfaces
                if eni_type in ['nat_gateway', 'vpc_endpoint', 'load_balancer', 'lambda']:
                    logger.debug(f"{prefix}Skipping AWS-managed network interface: {eni_id} (type: {eni_type})")
                    continue
                
                # Skip network interfaces attached to instances (they should be cleaned up with instances)
                if eni.get('Attachment', {}).get('InstanceId'):
                    logger.debug(f"{prefix}Skipping network interface attached to instance: {eni_id}")
                    continue
                
                logger.info(f"{prefix}Cleaning network interface: {eni_id} (status: {status})")
                
                if context and context.dry_run:
                    logger.info(f"{prefix}Would delete network interface: {eni_id}")
                    continue
                
                try:
                    # Detach if attached
                    if status == 'in-use' and 'Attachment' in eni:
                        attachment_id = eni['Attachment']['AttachmentId']
                        logger.info(f"{prefix}Detaching network interface: {eni_id}")
                        self.ec2_client.detach_network_interface(AttachmentId=attachment_id, Force=True)
                    
                    # Delete the network interface
                    self.ec2_client.delete_network_interface(NetworkInterfaceId=eni_id)
                    logger.info(f"{prefix}Deleted network interface: {eni_id}")
                
                except botocore.exceptions.ClientError as e:
                    logger.error(f"{prefix}Failed to clean network interface {eni_id}: {e}")
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"{prefix}Error listing network interfaces for subnet {self.subnet_id}: {e}")
    
    def _clean_route_table_associations(self, context: 'ExecutionContext' = None) -> None:
        """
        Clean up custom route table associations.
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        
        try:
            response = self.ec2_client.describe_route_tables(
                Filters=[
                    {'Name': 'association.subnet-id', 'Values': [self.subnet_id]}
                ]
            )
            
            for route_table in response['RouteTables']:
                route_table_id = route_table['RouteTableId']
                
                # Skip main route table
                is_main = any(assoc.get('Main', False) for assoc in route_table.get('Associations', []))
                if is_main:
                    logger.debug(f"{prefix}Skipping main route table: {route_table_id}")
                    continue
                
                # Find the association for this subnet
                for association in route_table.get('Associations', []):
                    if association.get('SubnetId') == self.subnet_id:
                        association_id = association['RouteTableAssociationId']
                        
                        logger.info(f"{prefix}Disassociating route table {route_table_id} from subnet {self.subnet_id}")
                        
                        if context and context.dry_run:
                            logger.info(f"{prefix}Would disassociate route table: {association_id}")
                            continue
                        
                        try:
                            self.ec2_client.disassociate_route_table(AssociationId=association_id)
                            logger.info(f"{prefix}Disassociated route table: {association_id}")
                        
                        except botocore.exceptions.ClientError as e:
                            logger.error(f"{prefix}Failed to disassociate route table {association_id}: {e}")
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"{prefix}Error listing route table associations for subnet {self.subnet_id}: {e}")
    
    def __str__(self) -> str:
        """String representation of the subnet resource."""
        return f"Subnet:{self.name}({self.subnet_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the subnet resource."""
        return (f"SubnetResource(subnet_id={self.subnet_id}, name={self.name}, "
                f"vpc_id={self.vpc_id}, az={self.availability_zone}, "
                f"cidr={self.cidr_block})")