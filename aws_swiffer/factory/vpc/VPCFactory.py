"""VPC Factory for creating VPC resource instances."""

import os
from typing import List, Type, Dict, Any
from abc import abstractmethod

from aws_swiffer.factory.BaseFactory import BaseFactory
from aws_swiffer.resources.IResource import IResource
from aws_swiffer.resources.vpc.VPCResource import VPCResource
from aws_swiffer.resources.vpc.SubnetResource import SubnetResource
from aws_swiffer.utils import get_logger, get_client

logger = get_logger(os.path.basename(__file__))


class VPCResourceCollection:
    """Collection of all resources in a VPC."""
    
    def __init__(self, vpc_id: str):
        """
        Initialize VPC resource collection.
        
        Args:
            vpc_id: VPC ID
        """
        self.vpc_id = vpc_id
        self.subnets: List[VPCResource] = []
        self.security_groups: List[VPCResource] = []
        self.route_tables: List[VPCResource] = []
        self.network_acls: List[VPCResource] = []
        self.network_interfaces: List[VPCResource] = []
        self.nat_gateways: List[VPCResource] = []
        self.vpc_endpoints: List[VPCResource] = []
        self.internet_gateways: List[VPCResource] = []
        self.elastic_ips: List[VPCResource] = []
        self.vpc_peering_connections: List[VPCResource] = []
    
    def get_all_resources(self) -> List[VPCResource]:
        """Get flat list of all resources."""
        all_resources = []
        all_resources.extend(self.subnets)
        all_resources.extend(self.security_groups)
        all_resources.extend(self.route_tables)
        all_resources.extend(self.network_acls)
        all_resources.extend(self.network_interfaces)
        all_resources.extend(self.nat_gateways)
        all_resources.extend(self.vpc_endpoints)
        all_resources.extend(self.internet_gateways)
        all_resources.extend(self.elastic_ips)
        all_resources.extend(self.vpc_peering_connections)
        return all_resources
    
    def filter_by_tags(self, tags: Dict[str, str]) -> 'VPCResourceCollection':
        """
        Filter resources by tags.
        
        Args:
            tags: Dictionary of tags to match
            
        Returns:
            New VPCResourceCollection with filtered resources
        """
        filtered = VPCResourceCollection(self.vpc_id)
        
        def matches_tags(resource: VPCResource) -> bool:
            if not resource.tags:
                return not tags  # If no tags required and resource has no tags, match
            
            resource_tag_dict = {tag.get('Key', ''): tag.get('Value', '') 
                               for tag in resource.tags if isinstance(tag, dict)}
            
            return all(resource_tag_dict.get(key) == value 
                      for key, value in tags.items())
        
        filtered.subnets = [r for r in self.subnets if matches_tags(r)]
        filtered.security_groups = [r for r in self.security_groups if matches_tags(r)]
        filtered.route_tables = [r for r in self.route_tables if matches_tags(r)]
        filtered.network_acls = [r for r in self.network_acls if matches_tags(r)]
        filtered.network_interfaces = [r for r in self.network_interfaces if matches_tags(r)]
        filtered.nat_gateways = [r for r in self.nat_gateways if matches_tags(r)]
        filtered.vpc_endpoints = [r for r in self.vpc_endpoints if matches_tags(r)]
        filtered.internet_gateways = [r for r in self.internet_gateways if matches_tags(r)]
        filtered.elastic_ips = [r for r in self.elastic_ips if matches_tags(r)]
        filtered.vpc_peering_connections = [r for r in self.vpc_peering_connections if matches_tags(r)]
        
        return filtered
    
    def exclude_default_resources(self) -> 'VPCResourceCollection':
        """
        Exclude default AWS resources.
        
        Returns:
            New VPCResourceCollection with default resources excluded
        """
        filtered = VPCResourceCollection(self.vpc_id)
        
        filtered.subnets = [r for r in self.subnets if not r.is_default_resource()]
        filtered.security_groups = [r for r in self.security_groups if not r.is_default_resource()]
        filtered.route_tables = [r for r in self.route_tables if not r.is_default_resource()]
        filtered.network_acls = [r for r in self.network_acls if not r.is_default_resource()]
        filtered.network_interfaces = [r for r in self.network_interfaces if not r.is_default_resource()]
        filtered.nat_gateways = [r for r in self.nat_gateways if not r.is_default_resource()]
        filtered.vpc_endpoints = [r for r in self.vpc_endpoints if not r.is_default_resource()]
        filtered.internet_gateways = [r for r in self.internet_gateways if not r.is_default_resource()]
        filtered.elastic_ips = [r for r in self.elastic_ips if not r.is_default_resource()]
        filtered.vpc_peering_connections = [r for r in self.vpc_peering_connections if not r.is_default_resource()]
        
        return filtered


class VPCFactory(BaseFactory):
    """Factory for creating VPC resource instances."""
    
    def __init__(self):
        """Initialize VPC factory."""
        super().__init__()
        self.ec2_client = get_client('ec2', self.region)
    
    def create_vpc_resources(self, vpc_id: str) -> VPCResourceCollection:
        """
        Discover and create all resources in a VPC.
        
        Args:
            vpc_id: VPC ID to discover resources for
            
        Returns:
            VPCResourceCollection containing all discovered resources
        """
        logger.info(f"Discovering resources in VPC: {vpc_id}")
        collection = VPCResourceCollection(vpc_id)
        
        # Discover subnets
        collection.subnets = self._discover_subnets(vpc_id)
        
        # TODO: Implement discovery for other resource types
        # This will be implemented in subsequent tasks
        logger.info(f"Discovered {len(collection.subnets)} subnets in VPC {vpc_id}")
        
        return collection
    
    def create_by_resource_type(self, vpc_id: str, resource_type: str) -> List[IResource]:
        """
        Create resources of specific type in VPC.
        
        Args:
            vpc_id: VPC ID
            resource_type: Type of resource to create
            
        Returns:
            List of resources of the specified type
        """
        collection = self.create_vpc_resources(vpc_id)
        
        type_mapping = {
            'subnet': collection.subnets,
            'security-group': collection.security_groups,
            'route-table': collection.route_tables,
            'network-acl': collection.network_acls,
            'network-interface': collection.network_interfaces,
            'nat-gateway': collection.nat_gateways,
            'vpc-endpoint': collection.vpc_endpoints,
            'internet-gateway': collection.internet_gateways,
            'elastic-ip': collection.elastic_ips,
            'vpc-peering-connection': collection.vpc_peering_connections
        }
        
        return type_mapping.get(resource_type, [])
    
    # Implement IFactory interface methods
    def create_by_tags(self, tags: dict) -> List[Type[IResource]]:
        """
        Create resources by tags.
        
        Args:
            tags: Dictionary of tags to match
            
        Returns:
            List of resources matching the tags
        """
        # TODO: Implement tag-based resource discovery
        logger.info(f"Creating VPC resources by tags: {tags}")
        return []
    
    def create_by_arn(self, arn: str) -> Type[IResource]:
        """
        Create resource by ARN.
        
        Args:
            arn: AWS Resource Name
            
        Returns:
            Resource instance
        """
        # TODO: Implement ARN-based resource creation
        logger.info(f"Creating VPC resource by ARN: {arn}")
        raise NotImplementedError("ARN-based resource creation not yet implemented")
    
    def create_by_name(self, name: str) -> Type[IResource]:
        """
        Create resource by name.
        
        Args:
            name: Resource name
            
        Returns:
            Resource instance
        """
        # TODO: Implement name-based resource creation
        logger.info(f"Creating VPC resource by name: {name}")
        raise NotImplementedError("Name-based resource creation not yet implemented")
    
    def create_by_id(self, resource_id: str) -> IResource:
        """
        Create resource by ID.
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Resource instance
        """
        # TODO: Implement ID-based resource creation
        logger.info(f"Creating VPC resource by ID: {resource_id}")
        raise NotImplementedError("ID-based resource creation not yet implemented")
    
    def _discover_subnets(self, vpc_id: str) -> List[SubnetResource]:
        """
        Discover all subnets in a VPC.
        
        Args:
            vpc_id: VPC ID to discover subnets for
            
        Returns:
            List of SubnetResource instances
        """
        logger.debug(f"Discovering subnets in VPC: {vpc_id}")
        subnets = []
        
        try:
            response = self.ec2_client.describe_subnets(
                Filters=[
                    {'Name': 'vpc-id', 'Values': [vpc_id]}
                ]
            )
            
            for subnet_data in response['Subnets']:
                subnet_id = subnet_data['SubnetId']
                availability_zone = subnet_data['AvailabilityZone']
                cidr_block = subnet_data['CidrBlock']
                tags = subnet_data.get('Tags', [])
                
                # Extract name from tags
                name = subnet_id  # Default to subnet ID
                for tag in tags:
                    if tag.get('Key', '').lower() == 'name':
                        name = tag.get('Value', subnet_id)
                        break
                
                # Construct ARN
                arn = f"arn:aws:ec2:{self.region}:{subnet_data.get('OwnerId', '')}:subnet/{subnet_id}"
                
                subnet_resource = SubnetResource(
                    arn=arn,
                    name=name,
                    vpc_id=vpc_id,
                    subnet_id=subnet_id,
                    availability_zone=availability_zone,
                    cidr_block=cidr_block,
                    tags=tags,
                    region=self.region
                )
                
                subnets.append(subnet_resource)
                logger.debug(f"Discovered subnet: {subnet_id} ({name}) in {availability_zone}")
        
        except Exception as e:
            logger.error(f"Error discovering subnets in VPC {vpc_id}: {e}")
        
        return subnets