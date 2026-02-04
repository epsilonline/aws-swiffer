"""VPC Endpoint Resource class for AWS Swiffer VPC resources."""

import os
import time
from typing import TYPE_CHECKING, Optional, List, Dict

import botocore.exceptions

from aws_swiffer.resources.vpc.VPCResource import VPCResource
from aws_swiffer.utils import get_client, get_logger

if TYPE_CHECKING:
    from aws_swiffer.utils.context import ExecutionContext

logger = get_logger(os.path.basename(__file__))


class VPCEndpointResource(VPCResource):
    """
    Represents a VPC Endpoint resource.
    
    VPC Endpoints provide private connectivity to AWS services without requiring
    internet access through NAT gateways or internet gateways.
    """
    
    def __init__(self, arn: str, name: str, vpc_id: str, vpc_endpoint_id: str,
                 service_name: str, vpc_endpoint_type: str, state: str,
                 subnet_ids: List[str] = None, route_table_ids: List[str] = None,
                 tags: list = None, region: str = None):
        """
        Initialize VPC Endpoint resource.
        
        Args:
            arn: AWS Resource Name
            name: VPC Endpoint name (from Name tag or endpoint ID)
            vpc_id: VPC ID this endpoint belongs to
            vpc_endpoint_id: VPC Endpoint ID
            service_name: AWS service name (e.g., com.amazonaws.us-east-1.s3)
            vpc_endpoint_type: Type of endpoint (Gateway, Interface, GatewayLoadBalancer)
            state: Current state (pending, available, deleting, deleted, failed)
            subnet_ids: List of subnet IDs (for Interface endpoints)
            route_table_ids: List of route table IDs (for Gateway endpoints)
            tags: Resource tags
            region: AWS region
        """
        super().__init__(
            arn=arn, 
            name=name, 
            vpc_id=vpc_id, 
            resource_type="vpc-endpoint",
            tags=tags, 
            region=region
        )
        self.vpc_endpoint_id = vpc_endpoint_id
        self.service_name = service_name
        self.vpc_endpoint_type = vpc_endpoint_type
        self.state = state
        self.subnet_ids = subnet_ids or []
        self.route_table_ids = route_table_ids or []
        self._ec2_client = None
    
    @property
    def ec2_client(self):
        """Lazy-loaded EC2 client."""
        if self._ec2_client is None:
            self._ec2_client = get_client('ec2', self.region)
        return self._ec2_client
    
    def is_default_resource(self) -> bool:
        """
        Check if this is a default VPC Endpoint.
        
        VPC Endpoints are always user-created resources, so there are no default
        VPC Endpoints to protect.
        
        Returns:
            False - VPC Endpoints are never default resources
        """
        return False
    
    def exists(self) -> bool:
        """
        Check if the VPC Endpoint still exists in AWS.
        
        Returns:
            True if VPC Endpoint exists, False otherwise
        """
        try:
            response = self.ec2_client.describe_vpc_endpoints(VpcEndpointIds=[self.vpc_endpoint_id])
            vpc_endpoints = response['VpcEndpoints']
            
            if not vpc_endpoints:
                return False
            
            # Check if VPC Endpoint is in a deleted state
            state = vpc_endpoints[0]['State']
            return state not in ['deleted', 'failed']
        
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidVpcEndpointId.NotFound':
                return False
            logger.error(f"Error checking VPC Endpoint existence: {e}")
            return True  # Assume exists if we can't determine
    
    def can_delete(self) -> bool:
        """
        Check if VPC Endpoint can be safely deleted.
        
        VPC Endpoints can generally be deleted unless they are in a transitional state.
        
        Returns:
            True if VPC Endpoint can be deleted, False otherwise
        """
        if not super().can_delete():
            return False
        
        # Check current state
        try:
            response = self.ec2_client.describe_vpc_endpoints(VpcEndpointIds=[self.vpc_endpoint_id])
            vpc_endpoints = response['VpcEndpoints']
            
            if not vpc_endpoints:
                logger.warning(f"VPC Endpoint {self.vpc_endpoint_id} not found")
                return False
            
            current_state = vpc_endpoints[0]['State']
            
            # Can only delete VPC Endpoints in available or failed state
            if current_state not in ['available', 'failed']:
                logger.warning(f"VPC Endpoint {self.vpc_endpoint_id} is in state '{current_state}' "
                             "and cannot be deleted")
                return False
            
            return True
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error checking VPC Endpoint {self.vpc_endpoint_id}: {e}")
            return False
    
    def remove(self, context: 'ExecutionContext' = None) -> None:
        """
        Remove the VPC Endpoint.
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Attempting to delete VPC Endpoint: {self.vpc_endpoint_id} ({self.name})")
        
        # Check if we can delete this VPC Endpoint
        if not self.can_delete():
            logger.error(f"Cannot delete VPC Endpoint {self.vpc_endpoint_id} - "
                        "it's in invalid state")
            return
        
        operation_desc = f"delete VPC Endpoint {self.vpc_endpoint_id} ({self.name}) in VPC {self.vpc_id}"
        
        if not self._should_proceed(context, operation_desc):
            logger.info("VPC Endpoint deletion skipped")
            return
        
        if context and context.dry_run:
            logger.info(f"{prefix}Would delete VPC Endpoint: {self.vpc_endpoint_id}")
            return
        
        try:
            response = self.ec2_client.delete_vpc_endpoints(VpcEndpointIds=[self.vpc_endpoint_id])
            
            # Check if deletion was successful
            unsuccessful = response.get('Unsuccessful', [])
            if unsuccessful:
                error_info = unsuccessful[0]
                error_code = error_info.get('Error', {}).get('Code', 'Unknown')
                error_message = error_info.get('Error', {}).get('Message', 'Unknown error')
                logger.error(f"{prefix}Failed to delete VPC Endpoint {self.vpc_endpoint_id}: "
                           f"{error_code} - {error_message}")
                return
            
            logger.info(f"{prefix}Initiated deletion of VPC Endpoint: {self.vpc_endpoint_id}")
            
            # Wait for deletion to complete if requested
            if context and hasattr(context, 'wait_for_completion') and context.wait_for_completion:
                self._wait_for_deletion(context)
        
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'InvalidVpcEndpointId.NotFound':
                logger.warning(f"{prefix}VPC Endpoint {self.vpc_endpoint_id} not found - "
                             "may have been deleted already")
            else:
                logger.error(f"{prefix}Failed to delete VPC Endpoint {self.vpc_endpoint_id}: "
                           f"{error_code} - {error_message}")
            
            logger.debug(f"Full error details: {e}")
    
    def _wait_for_deletion(self, context: 'ExecutionContext' = None, max_wait_time: int = 300) -> None:
        """
        Wait for VPC Endpoint deletion to complete.
        
        Args:
            context: ExecutionContext for logging
            max_wait_time: Maximum time to wait in seconds (default: 5 minutes)
        """
        prefix = context.log_prefix() if context else ""
        start_time = time.time()
        
        logger.info(f"{prefix}Waiting for VPC Endpoint {self.vpc_endpoint_id} deletion to complete...")
        
        while time.time() - start_time < max_wait_time:
            try:
                response = self.ec2_client.describe_vpc_endpoints(VpcEndpointIds=[self.vpc_endpoint_id])
                vpc_endpoints = response['VpcEndpoints']
                
                if not vpc_endpoints:
                    logger.info(f"{prefix}VPC Endpoint {self.vpc_endpoint_id} deleted successfully")
                    return
                
                state = vpc_endpoints[0]['State']
                
                if state == 'deleted':
                    logger.info(f"{prefix}VPC Endpoint {self.vpc_endpoint_id} deleted successfully")
                    return
                elif state == 'failed':
                    logger.error(f"{prefix}VPC Endpoint {self.vpc_endpoint_id} deletion failed")
                    return
                elif state == 'deleting':
                    logger.debug(f"{prefix}VPC Endpoint {self.vpc_endpoint_id} is still deleting...")
                else:
                    logger.warning(f"{prefix}VPC Endpoint {self.vpc_endpoint_id} in unexpected state: {state}")
                
                time.sleep(10)  # Wait 10 seconds between checks
            
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'InvalidVpcEndpointId.NotFound':
                    logger.info(f"{prefix}VPC Endpoint {self.vpc_endpoint_id} deleted successfully")
                    return
                logger.error(f"{prefix}Error checking VPC Endpoint deletion status: {e}")
                break
        
        logger.warning(f"{prefix}Timeout waiting for VPC Endpoint {self.vpc_endpoint_id} deletion")
    
    def clean(self, context: 'ExecutionContext' = None) -> None:
        """
        Clean VPC Endpoint dependencies before deletion.
        
        VPC Endpoints typically don't have dependencies that prevent deletion,
        but this method is provided for consistency with other resource types.
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Cleaning dependencies for VPC Endpoint: {self.vpc_endpoint_id}")
        
        # VPC Endpoints generally don't have dependencies that prevent deletion
        # The endpoint itself manages its network interfaces and route table entries
        logger.debug(f"{prefix}VPC Endpoint {self.vpc_endpoint_id} has no dependencies to clean")
    
    def get_endpoint_details(self) -> Dict:
        """
        Get detailed information about the VPC Endpoint.
        
        Returns:
            Dictionary containing endpoint details
        """
        try:
            response = self.ec2_client.describe_vpc_endpoints(VpcEndpointIds=[self.vpc_endpoint_id])
            vpc_endpoints = response['VpcEndpoints']
            
            if vpc_endpoints:
                endpoint = vpc_endpoints[0]
                return {
                    'vpc_endpoint_id': endpoint['VpcEndpointId'],
                    'service_name': endpoint['ServiceName'],
                    'vpc_endpoint_type': endpoint['VpcEndpointType'],
                    'state': endpoint['State'],
                    'subnet_ids': endpoint.get('SubnetIds', []),
                    'route_table_ids': endpoint.get('RouteTableIds', []),
                    'network_interface_ids': endpoint.get('NetworkInterfaceIds', []),
                    'dns_entries': endpoint.get('DnsEntries', []),
                    'creation_timestamp': endpoint.get('CreationTimestamp'),
                    'policy_document': endpoint.get('PolicyDocument')
                }
            
            return {}
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error getting VPC Endpoint details for {self.vpc_endpoint_id}: {e}")
            return {}
    
    def is_gateway_endpoint(self) -> bool:
        """
        Check if this is a Gateway VPC Endpoint.
        
        Returns:
            True if this is a Gateway endpoint, False otherwise
        """
        return self.vpc_endpoint_type.lower() == 'gateway'
    
    def is_interface_endpoint(self) -> bool:
        """
        Check if this is an Interface VPC Endpoint.
        
        Returns:
            True if this is an Interface endpoint, False otherwise
        """
        return self.vpc_endpoint_type.lower() == 'interface'
    
    def is_gateway_load_balancer_endpoint(self) -> bool:
        """
        Check if this is a Gateway Load Balancer VPC Endpoint.
        
        Returns:
            True if this is a Gateway Load Balancer endpoint, False otherwise
        """
        return self.vpc_endpoint_type.lower() == 'gatewayloadbalancer'
    
    def __str__(self) -> str:
        """String representation of the VPC Endpoint resource."""
        return f"VPCEndpoint:{self.name}({self.vpc_endpoint_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the VPC Endpoint resource."""
        return (f"VPCEndpointResource(vpc_endpoint_id={self.vpc_endpoint_id}, name={self.name}, "
                f"vpc_id={self.vpc_id}, service_name={self.service_name}, "
                f"type={self.vpc_endpoint_type}, state={self.state})")