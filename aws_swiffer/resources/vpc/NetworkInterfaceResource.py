"""Network Interface Resource class for AWS Swiffer VPC resources."""

import os
import time
from typing import TYPE_CHECKING, Optional, List, Dict

import botocore.exceptions

from aws_swiffer.resources.vpc.VPCResource import VPCResource
from aws_swiffer.utils import get_client, get_logger

if TYPE_CHECKING:
    from aws_swiffer.utils.context import ExecutionContext

logger = get_logger(os.path.basename(__file__))


class NetworkInterfaceResource(VPCResource):
    """
    Represents a VPC network interface (ENI) resource.
    
    Network interfaces provide network connectivity to EC2 instances and other
    AWS services within a VPC.
    """
    
    def __init__(self, arn: str, name: str, vpc_id: str, network_interface_id: str,
                 subnet_id: str, interface_type: str, status: str, 
                 private_ip_address: str = None, tags: list = None, region: str = None):
        """
        Initialize network interface resource.
        
        Args:
            arn: AWS Resource Name
            name: Network interface name (from Name tag or interface ID)
            vpc_id: VPC ID this network interface belongs to
            network_interface_id: Network interface ID
            subnet_id: Subnet ID where the interface is located
            interface_type: Type of interface (interface, nat_gateway, vpc_endpoint, etc.)
            status: Current status (available, in-use, etc.)
            private_ip_address: Primary private IP address
            tags: Resource tags
            region: AWS region
        """
        super().__init__(
            arn=arn, 
            name=name, 
            vpc_id=vpc_id, 
            resource_type="network-interface",
            tags=tags, 
            region=region
        )
        self.network_interface_id = network_interface_id
        self.subnet_id = subnet_id
        self.interface_type = interface_type
        self.status = status
        self.private_ip_address = private_ip_address
        self._ec2_client = None
    
    @property
    def ec2_client(self):
        """Lazy-loaded EC2 client."""
        if self._ec2_client is None:
            self._ec2_client = get_client('ec2', self.region)
        return self._ec2_client
    
    def is_default_resource(self) -> bool:
        """
        Check if this is a default or AWS-managed network interface.
        
        AWS-managed network interfaces (for NAT gateways, VPC endpoints, load balancers, etc.)
        should be protected from direct deletion as they are managed by their parent services.
        
        Returns:
            True if this is an AWS-managed network interface, False otherwise
        """
        # AWS-managed interface types that should not be deleted directly
        aws_managed_types = {
            'nat_gateway',
            'vpc_endpoint', 
            'load_balancer',
            'lambda',
            'efs',
            'rds',
            'elasticache',
            'redshift',
            'workspaces',
            'directory_service'
        }
        
        is_managed = self.interface_type in aws_managed_types
        
        if is_managed:
            logger.warning(f"Network interface {self.network_interface_id} is AWS-managed "
                         f"(type: {self.interface_type}) and is protected")
        
        return is_managed
    
    def exists(self) -> bool:
        """
        Check if the network interface still exists in AWS.
        
        Returns:
            True if network interface exists, False otherwise
        """
        try:
            self.ec2_client.describe_network_interfaces(NetworkInterfaceIds=[self.network_interface_id])
            return True
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidNetworkInterfaceID.NotFound':
                return False
            logger.error(f"Error checking network interface existence: {e}")
            return True  # Assume exists if we can't determine
    
    def can_delete(self) -> bool:
        """
        Check if network interface can be safely deleted.
        
        Network interfaces cannot be deleted if:
        - They are AWS-managed (NAT gateway, VPC endpoint, etc.)
        - They are attached to running instances
        - They are the primary interface of an instance
        
        Returns:
            True if network interface can be deleted, False otherwise
        """
        if not super().can_delete():
            return False
        
        # Get current status
        try:
            response = self.ec2_client.describe_network_interfaces(
                NetworkInterfaceIds=[self.network_interface_id]
            )
            eni = response['NetworkInterfaces'][0]
            current_status = eni['Status']
            attachment = eni.get('Attachment', {})
            
            # Check if attached to an instance
            if attachment and attachment.get('InstanceId'):
                instance_id = attachment['InstanceId']
                device_index = attachment.get('DeviceIndex', 0)
                
                # Primary network interfaces (device index 0) cannot be detached
                if device_index == 0:
                    logger.warning(f"Network interface {self.network_interface_id} is the primary "
                                 f"interface for instance {instance_id} and cannot be deleted")
                    return False
                
                # Check if instance is running
                try:
                    instance_response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
                    instance = instance_response['Reservations'][0]['Instances'][0]
                    instance_state = instance['State']['Name']
                    
                    if instance_state in ['pending', 'running', 'stopping']:
                        logger.warning(f"Network interface {self.network_interface_id} is attached "
                                     f"to running instance {instance_id} (state: {instance_state})")
                        return False
                
                except botocore.exceptions.ClientError as e:
                    logger.error(f"Error checking instance state for {instance_id}: {e}")
                    return False
            
            return True
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error checking network interface {self.network_interface_id}: {e}")
            return False
    
    def remove(self, context: 'ExecutionContext' = None) -> None:
        """
        Remove the network interface.
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Attempting to delete network interface: {self.network_interface_id} ({self.name})")
        
        # Check if we can delete this network interface
        if not self.can_delete():
            logger.error(f"Cannot delete network interface {self.network_interface_id} - "
                        "dependencies exist or it's protected")
            return
        
        operation_desc = f"delete network interface {self.network_interface_id} ({self.name}) in VPC {self.vpc_id}"
        
        if not self._should_proceed(context, operation_desc):
            logger.info("Network interface deletion skipped")
            return
        
        if context and context.dry_run:
            logger.info(f"{prefix}Would delete network interface: {self.network_interface_id}")
            return
        
        # Detach if necessary before deletion
        self._detach_if_needed(context)
        
        try:
            self.ec2_client.delete_network_interface(NetworkInterfaceId=self.network_interface_id)
            logger.info(f"{prefix}Successfully deleted network interface: {self.network_interface_id}")
        
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'InvalidNetworkInterfaceID.NotFound':
                logger.warning(f"{prefix}Network interface {self.network_interface_id} not found - "
                             "may have been deleted already")
            elif error_code == 'InvalidNetworkInterface.InUse':
                logger.error(f"{prefix}Cannot delete network interface {self.network_interface_id} - "
                           f"interface is in use: {error_message}")
            elif error_code == 'DependencyViolation':
                logger.error(f"{prefix}Cannot delete network interface {self.network_interface_id} - "
                           f"dependency violation: {error_message}")
            else:
                logger.error(f"{prefix}Failed to delete network interface {self.network_interface_id}: "
                           f"{error_code} - {error_message}")
            
            logger.debug(f"Full error details: {e}")
    
    def _detach_if_needed(self, context: 'ExecutionContext' = None) -> None:
        """
        Detach network interface if it's attached to an instance.
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        
        try:
            response = self.ec2_client.describe_network_interfaces(
                NetworkInterfaceIds=[self.network_interface_id]
            )
            eni = response['NetworkInterfaces'][0]
            attachment = eni.get('Attachment', {})
            
            if attachment and attachment.get('AttachmentId'):
                attachment_id = attachment['AttachmentId']
                instance_id = attachment.get('InstanceId')
                device_index = attachment.get('DeviceIndex', 0)
                
                # Don't detach primary interfaces (device index 0)
                if device_index == 0:
                    logger.debug(f"{prefix}Skipping detachment of primary network interface")
                    return
                
                logger.info(f"{prefix}Detaching network interface {self.network_interface_id} "
                          f"from instance {instance_id}")
                
                if context and context.dry_run:
                    logger.info(f"{prefix}Would detach network interface: {self.network_interface_id}")
                    return
                
                try:
                    self.ec2_client.detach_network_interface(
                        AttachmentId=attachment_id,
                        Force=True
                    )
                    
                    # Wait for detachment to complete
                    self._wait_for_detachment(attachment_id, context)
                    
                    logger.info(f"{prefix}Successfully detached network interface: {self.network_interface_id}")
                
                except botocore.exceptions.ClientError as e:
                    logger.error(f"{prefix}Failed to detach network interface {self.network_interface_id}: {e}")
                    raise
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"{prefix}Error checking attachment status for {self.network_interface_id}: {e}")
    
    def _wait_for_detachment(self, attachment_id: str, context: 'ExecutionContext' = None, 
                           max_wait_time: int = 60) -> None:
        """
        Wait for network interface detachment to complete.
        
        Args:
            attachment_id: Attachment ID to wait for
            context: ExecutionContext for logging
            max_wait_time: Maximum time to wait in seconds
        """
        prefix = context.log_prefix() if context else ""
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = self.ec2_client.describe_network_interfaces(
                    NetworkInterfaceIds=[self.network_interface_id]
                )
                eni = response['NetworkInterfaces'][0]
                
                # Check if still attached
                if not eni.get('Attachment'):
                    logger.debug(f"{prefix}Network interface {self.network_interface_id} detached successfully")
                    return
                
                # Check attachment status
                attachment = eni.get('Attachment', {})
                if attachment.get('Status') == 'detached':
                    logger.debug(f"{prefix}Network interface {self.network_interface_id} detached successfully")
                    return
                
                time.sleep(2)
            
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'InvalidNetworkInterfaceID.NotFound':
                    # Interface was deleted, which means detachment succeeded
                    return
                logger.error(f"{prefix}Error checking detachment status: {e}")
                break
        
        logger.warning(f"{prefix}Timeout waiting for network interface {self.network_interface_id} to detach")
    
    def clean(self, context: 'ExecutionContext' = None) -> None:
        """
        Clean network interface dependencies before deletion.
        
        This method handles cleanup of resources that prevent network interface deletion:
        - Detach from instances if attached
        - Release associated Elastic IPs
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Cleaning dependencies for network interface: {self.network_interface_id}")
        
        # Clean up Elastic IP associations
        self._clean_elastic_ip_associations(context)
        
        # Detach from instance if needed
        self._detach_if_needed(context)
    
    def _clean_elastic_ip_associations(self, context: 'ExecutionContext' = None) -> None:
        """
        Clean up Elastic IP associations.
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        
        try:
            response = self.ec2_client.describe_network_interfaces(
                NetworkInterfaceIds=[self.network_interface_id]
            )
            eni = response['NetworkInterfaces'][0]
            
            # Check for associated Elastic IPs
            for private_ip in eni.get('PrivateIpAddresses', []):
                association = private_ip.get('Association', {})
                if association and association.get('AssociationId'):
                    association_id = association['AssociationId']
                    public_ip = association.get('PublicIp')
                    
                    logger.info(f"{prefix}Disassociating Elastic IP {public_ip} from network interface "
                              f"{self.network_interface_id}")
                    
                    if context and context.dry_run:
                        logger.info(f"{prefix}Would disassociate Elastic IP: {association_id}")
                        continue
                    
                    try:
                        self.ec2_client.disassociate_address(AssociationId=association_id)
                        logger.info(f"{prefix}Disassociated Elastic IP: {association_id}")
                    
                    except botocore.exceptions.ClientError as e:
                        logger.error(f"{prefix}Failed to disassociate Elastic IP {association_id}: {e}")
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"{prefix}Error checking Elastic IP associations for {self.network_interface_id}: {e}")
    
    def __str__(self) -> str:
        """String representation of the network interface resource."""
        return f"NetworkInterface:{self.name}({self.network_interface_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the network interface resource."""
        return (f"NetworkInterfaceResource(eni_id={self.network_interface_id}, name={self.name}, "
                f"vpc_id={self.vpc_id}, subnet_id={self.subnet_id}, type={self.interface_type}, "
                f"status={self.status})")