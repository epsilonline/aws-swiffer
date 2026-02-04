"""NAT Gateway Resource class for AWS Swiffer VPC resources."""

import os
import time
from typing import TYPE_CHECKING, Optional, List, Dict

import botocore.exceptions

from aws_swiffer.resources.vpc.VPCResource import VPCResource
from aws_swiffer.utils import get_client, get_logger

if TYPE_CHECKING:
    from aws_swiffer.utils.context import ExecutionContext

logger = get_logger(os.path.basename(__file__))


class NATGatewayResource(VPCResource):
    """
    Represents a VPC NAT Gateway resource.
    
    NAT Gateways provide outbound internet connectivity for resources in private subnets
    while preventing inbound connections from the internet.
    """
    
    def __init__(self, arn: str, name: str, vpc_id: str, nat_gateway_id: str,
                 subnet_id: str, state: str, nat_gateway_type: str = "public",
                 connectivity_type: str = "public", tags: list = None, region: str = None):
        """
        Initialize NAT Gateway resource.
        
        Args:
            arn: AWS Resource Name
            name: NAT Gateway name (from Name tag or NAT Gateway ID)
            vpc_id: VPC ID this NAT Gateway belongs to
            nat_gateway_id: NAT Gateway ID
            subnet_id: Subnet ID where the NAT Gateway is located
            state: Current state (pending, available, deleting, deleted, failed)
            nat_gateway_type: Type of NAT Gateway (public, private)
            connectivity_type: Connectivity type (public, private)
            tags: Resource tags
            region: AWS region
        """
        super().__init__(
            arn=arn, 
            name=name, 
            vpc_id=vpc_id, 
            resource_type="nat-gateway",
            tags=tags, 
            region=region
        )
        self.nat_gateway_id = nat_gateway_id
        self.subnet_id = subnet_id
        self.state = state
        self.nat_gateway_type = nat_gateway_type
        self.connectivity_type = connectivity_type
        self._ec2_client = None
    
    @property
    def ec2_client(self):
        """Lazy-loaded EC2 client."""
        if self._ec2_client is None:
            self._ec2_client = get_client('ec2', self.region)
        return self._ec2_client
    
    def is_default_resource(self) -> bool:
        """
        Check if this is a default NAT Gateway.
        
        NAT Gateways are always user-created resources, so there are no default
        NAT Gateways to protect.
        
        Returns:
            False - NAT Gateways are never default resources
        """
        return False
    
    def exists(self) -> bool:
        """
        Check if the NAT Gateway still exists in AWS.
        
        Returns:
            True if NAT Gateway exists, False otherwise
        """
        try:
            response = self.ec2_client.describe_nat_gateways(NatGatewayIds=[self.nat_gateway_id])
            nat_gateways = response['NatGateways']
            
            if not nat_gateways:
                return False
            
            # Check if NAT Gateway is in a deleted state
            state = nat_gateways[0]['State']
            return state not in ['deleted', 'failed']
        
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidNatGatewayID.NotFound':
                return False
            logger.error(f"Error checking NAT Gateway existence: {e}")
            return True  # Assume exists if we can't determine
    
    def can_delete(self) -> bool:
        """
        Check if NAT Gateway can be safely deleted.
        
        NAT Gateways can generally be deleted unless they are in a transitional state
        or have dependencies that prevent deletion.
        
        Returns:
            True if NAT Gateway can be deleted, False otherwise
        """
        if not super().can_delete():
            return False
        
        # Check current state
        try:
            response = self.ec2_client.describe_nat_gateways(NatGatewayIds=[self.nat_gateway_id])
            nat_gateways = response['NatGateways']
            
            if not nat_gateways:
                logger.warning(f"NAT Gateway {self.nat_gateway_id} not found")
                return False
            
            current_state = nat_gateways[0]['State']
            
            # Can only delete NAT Gateways in available or failed state
            if current_state not in ['available', 'failed']:
                logger.warning(f"NAT Gateway {self.nat_gateway_id} is in state '{current_state}' "
                             "and cannot be deleted")
                return False
            
            # Check for route table references
            if not self._check_route_table_references():
                return False
            
            return True
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error checking NAT Gateway {self.nat_gateway_id}: {e}")
            return False
    
    def _check_route_table_references(self) -> bool:
        """
        Check if any route tables reference this NAT Gateway.
        
        Returns:
            True if no references found, False if references exist
        """
        try:
            response = self.ec2_client.describe_route_tables(
                Filters=[
                    {'Name': 'vpc-id', 'Values': [self.vpc_id]}
                ]
            )
            
            for route_table in response['RouteTables']:
                for route in route_table.get('Routes', []):
                    if route.get('NatGatewayId') == self.nat_gateway_id:
                        route_table_id = route_table['RouteTableId']
                        destination = route.get('DestinationCidrBlock', route.get('DestinationIpv6CidrBlock', 'unknown'))
                        logger.warning(f"NAT Gateway {self.nat_gateway_id} is referenced by route table "
                                     f"{route_table_id} for destination {destination}")
                        return False
            
            return True
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"Error checking route table references for NAT Gateway {self.nat_gateway_id}: {e}")
            return False
    
    def remove(self, context: 'ExecutionContext' = None) -> None:
        """
        Remove the NAT Gateway.
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Attempting to delete NAT Gateway: {self.nat_gateway_id} ({self.name})")
        
        # Check if we can delete this NAT Gateway
        if not self.can_delete():
            logger.error(f"Cannot delete NAT Gateway {self.nat_gateway_id} - "
                        "dependencies exist or it's in invalid state")
            return
        
        operation_desc = f"delete NAT Gateway {self.nat_gateway_id} ({self.name}) in VPC {self.vpc_id}"
        
        if not self._should_proceed(context, operation_desc):
            logger.info("NAT Gateway deletion skipped")
            return
        
        if context and context.dry_run:
            logger.info(f"{prefix}Would delete NAT Gateway: {self.nat_gateway_id}")
            return
        
        try:
            response = self.ec2_client.delete_nat_gateway(NatGatewayId=self.nat_gateway_id)
            logger.info(f"{prefix}Initiated deletion of NAT Gateway: {self.nat_gateway_id}")
            
            # Wait for deletion to complete if requested
            if context and hasattr(context, 'wait_for_completion') and context.wait_for_completion:
                self._wait_for_deletion(context)
        
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'InvalidNatGatewayID.NotFound':
                logger.warning(f"{prefix}NAT Gateway {self.nat_gateway_id} not found - "
                             "may have been deleted already")
            elif error_code == 'DependencyViolation':
                logger.error(f"{prefix}Cannot delete NAT Gateway {self.nat_gateway_id} - "
                           f"dependency violation: {error_message}")
            elif error_code == 'InvalidNatGateway.InUse':
                logger.error(f"{prefix}Cannot delete NAT Gateway {self.nat_gateway_id} - "
                           f"gateway is in use: {error_message}")
            else:
                logger.error(f"{prefix}Failed to delete NAT Gateway {self.nat_gateway_id}: "
                           f"{error_code} - {error_message}")
            
            logger.debug(f"Full error details: {e}")
    
    def _wait_for_deletion(self, context: 'ExecutionContext' = None, max_wait_time: int = 300) -> None:
        """
        Wait for NAT Gateway deletion to complete.
        
        Args:
            context: ExecutionContext for logging
            max_wait_time: Maximum time to wait in seconds (default: 5 minutes)
        """
        prefix = context.log_prefix() if context else ""
        start_time = time.time()
        
        logger.info(f"{prefix}Waiting for NAT Gateway {self.nat_gateway_id} deletion to complete...")
        
        while time.time() - start_time < max_wait_time:
            try:
                response = self.ec2_client.describe_nat_gateways(NatGatewayIds=[self.nat_gateway_id])
                nat_gateways = response['NatGateways']
                
                if not nat_gateways:
                    logger.info(f"{prefix}NAT Gateway {self.nat_gateway_id} deleted successfully")
                    return
                
                state = nat_gateways[0]['State']
                
                if state == 'deleted':
                    logger.info(f"{prefix}NAT Gateway {self.nat_gateway_id} deleted successfully")
                    return
                elif state == 'failed':
                    logger.error(f"{prefix}NAT Gateway {self.nat_gateway_id} deletion failed")
                    return
                elif state == 'deleting':
                    logger.debug(f"{prefix}NAT Gateway {self.nat_gateway_id} is still deleting...")
                else:
                    logger.warning(f"{prefix}NAT Gateway {self.nat_gateway_id} in unexpected state: {state}")
                
                time.sleep(10)  # Wait 10 seconds between checks
            
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'InvalidNatGatewayID.NotFound':
                    logger.info(f"{prefix}NAT Gateway {self.nat_gateway_id} deleted successfully")
                    return
                logger.error(f"{prefix}Error checking NAT Gateway deletion status: {e}")
                break
        
        logger.warning(f"{prefix}Timeout waiting for NAT Gateway {self.nat_gateway_id} deletion")
    
    def clean(self, context: 'ExecutionContext' = None) -> None:
        """
        Clean NAT Gateway dependencies before deletion.
        
        This method handles cleanup of resources that prevent NAT Gateway deletion:
        - Remove routes that reference this NAT Gateway
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        logger.info(f"{prefix}Cleaning dependencies for NAT Gateway: {self.nat_gateway_id}")
        
        # Clean up route table references
        self._clean_route_table_references(context)
    
    def _clean_route_table_references(self, context: 'ExecutionContext' = None) -> None:
        """
        Clean up route table references to this NAT Gateway.
        
        Args:
            context: ExecutionContext for dry-run and auto-approve modes
        """
        prefix = context.log_prefix() if context else ""
        
        try:
            response = self.ec2_client.describe_route_tables(
                Filters=[
                    {'Name': 'vpc-id', 'Values': [self.vpc_id]}
                ]
            )
            
            for route_table in response['RouteTables']:
                route_table_id = route_table['RouteTableId']
                routes_to_delete = []
                
                for route in route_table.get('Routes', []):
                    if route.get('NatGatewayId') == self.nat_gateway_id:
                        destination = route.get('DestinationCidrBlock') or route.get('DestinationIpv6CidrBlock')
                        if destination:
                            routes_to_delete.append({
                                'destination': destination,
                                'is_ipv6': 'DestinationIpv6CidrBlock' in route
                            })
                
                # Delete routes that reference this NAT Gateway
                for route_info in routes_to_delete:
                    destination = route_info['destination']
                    is_ipv6 = route_info['is_ipv6']
                    
                    logger.info(f"{prefix}Removing route to {destination} via NAT Gateway "
                              f"{self.nat_gateway_id} from route table {route_table_id}")
                    
                    if context and context.dry_run:
                        logger.info(f"{prefix}Would remove route: {destination} -> {self.nat_gateway_id}")
                        continue
                    
                    try:
                        if is_ipv6:
                            self.ec2_client.delete_route(
                                RouteTableId=route_table_id,
                                DestinationIpv6CidrBlock=destination
                            )
                        else:
                            self.ec2_client.delete_route(
                                RouteTableId=route_table_id,
                                DestinationCidrBlock=destination
                            )
                        
                        logger.info(f"{prefix}Removed route: {destination} -> {self.nat_gateway_id}")
                    
                    except botocore.exceptions.ClientError as e:
                        error_code = e.response['Error']['Code']
                        if error_code == 'InvalidRoute.NotFound':
                            logger.debug(f"{prefix}Route {destination} -> {self.nat_gateway_id} "
                                       "not found - may have been removed already")
                        else:
                            logger.error(f"{prefix}Failed to remove route {destination} -> "
                                       f"{self.nat_gateway_id}: {e}")
        
        except botocore.exceptions.ClientError as e:
            logger.error(f"{prefix}Error cleaning route table references for NAT Gateway "
                        f"{self.nat_gateway_id}: {e}")
    
    def __str__(self) -> str:
        """String representation of the NAT Gateway resource."""
        return f"NATGateway:{self.name}({self.nat_gateway_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the NAT Gateway resource."""
        return (f"NATGatewayResource(nat_gateway_id={self.nat_gateway_id}, name={self.name}, "
                f"vpc_id={self.vpc_id}, subnet_id={self.subnet_id}, state={self.state}, "
                f"type={self.nat_gateway_type})")