"""Unit tests for SubnetResource class."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import botocore.exceptions

from aws_swiffer.resources.vpc.SubnetResource import SubnetResource
from aws_swiffer.utils.context import ExecutionContext


class TestSubnetResource(unittest.TestCase):
    """Test cases for SubnetResource class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.subnet_resource = SubnetResource(
            arn="arn:aws:ec2:us-east-1:123456789012:subnet/subnet-12345678",
            name="test-subnet",
            vpc_id="vpc-12345678",
            subnet_id="subnet-12345678",
            availability_zone="us-east-1a",
            cidr_block="10.0.1.0/24",
            tags=[{"Key": "Name", "Value": "test-subnet"}],
            region="us-east-1"
        )
    
    def test_initialization(self):
        """Test subnet resource initialization."""
        self.assertEqual(self.subnet_resource.subnet_id, "subnet-12345678")
        self.assertEqual(self.subnet_resource.vpc_id, "vpc-12345678")
        self.assertEqual(self.subnet_resource.availability_zone, "us-east-1a")
        self.assertEqual(self.subnet_resource.cidr_block, "10.0.1.0/24")
        self.assertEqual(self.subnet_resource.resource_type, "subnet")
        self.assertEqual(self.subnet_resource.name, "test-subnet")
    
    @patch('aws_swiffer.resources.vpc.SubnetResource.get_client')
    def test_is_default_resource_true(self, mock_get_client):
        """Test is_default_resource returns True for default subnets."""
        mock_ec2 = Mock()
        mock_get_client.return_value = mock_ec2
        mock_ec2.describe_subnets.return_value = {
            'Subnets': [{'DefaultForAz': True}]
        }
        
        result = self.subnet_resource.is_default_resource()
        
        self.assertTrue(result)
        mock_ec2.describe_subnets.assert_called_once_with(SubnetIds=["subnet-12345678"])
    
    @patch('aws_swiffer.resources.vpc.SubnetResource.get_client')
    def test_is_default_resource_false(self, mock_get_client):
        """Test is_default_resource returns False for custom subnets."""
        mock_ec2 = Mock()
        mock_get_client.return_value = mock_ec2
        mock_ec2.describe_subnets.return_value = {
            'Subnets': [{'DefaultForAz': False}]
        }
        
        result = self.subnet_resource.is_default_resource()
        
        self.assertFalse(result)
    
    @patch('aws_swiffer.resources.vpc.SubnetResource.get_client')
    def test_exists_true(self, mock_get_client):
        """Test exists returns True when subnet exists."""
        mock_ec2 = Mock()
        mock_get_client.return_value = mock_ec2
        mock_ec2.describe_subnets.return_value = {'Subnets': [{}]}
        
        result = self.subnet_resource.exists()
        
        self.assertTrue(result)
    
    @patch('aws_swiffer.resources.vpc.SubnetResource.get_client')
    def test_exists_false(self, mock_get_client):
        """Test exists returns False when subnet doesn't exist."""
        mock_ec2 = Mock()
        mock_get_client.return_value = mock_ec2
        error = botocore.exceptions.ClientError(
            {'Error': {'Code': 'InvalidSubnetID.NotFound'}}, 
            'describe_subnets'
        )
        mock_ec2.describe_subnets.side_effect = error
        
        result = self.subnet_resource.exists()
        
        self.assertFalse(result)
    
    @patch('aws_swiffer.resources.vpc.SubnetResource.get_client')
    def test_can_delete_with_network_interfaces(self, mock_get_client):
        """Test can_delete returns False when subnet has network interfaces."""
        mock_ec2 = Mock()
        mock_get_client.return_value = mock_ec2
        
        # Mock subnet as non-default
        mock_ec2.describe_subnets.return_value = {
            'Subnets': [{'DefaultForAz': False}]
        }
        
        # Mock network interfaces exist
        mock_ec2.describe_network_interfaces.return_value = {
            'NetworkInterfaces': [{'NetworkInterfaceId': 'eni-12345678'}]
        }
        
        result = self.subnet_resource.can_delete()
        
        self.assertFalse(result)
    
    @patch('aws_swiffer.resources.vpc.SubnetResource.get_client')
    def test_can_delete_with_instances(self, mock_get_client):
        """Test can_delete returns False when subnet has instances."""
        mock_ec2 = Mock()
        mock_get_client.return_value = mock_ec2
        
        # Mock subnet as non-default
        mock_ec2.describe_subnets.return_value = {
            'Subnets': [{'DefaultForAz': False}]
        }
        
        # Mock no network interfaces
        mock_ec2.describe_network_interfaces.return_value = {
            'NetworkInterfaces': []
        }
        
        # Mock instances exist
        mock_ec2.describe_instances.return_value = {
            'Reservations': [
                {'Instances': [{'InstanceId': 'i-12345678', 'State': {'Name': 'running'}}]}
            ]
        }
        
        result = self.subnet_resource.can_delete()
        
        self.assertFalse(result)
    
    @patch('aws_swiffer.resources.vpc.SubnetResource.get_client')
    def test_can_delete_success(self, mock_get_client):
        """Test can_delete returns True when subnet can be deleted."""
        mock_ec2 = Mock()
        mock_get_client.return_value = mock_ec2
        
        # Mock subnet as non-default
        mock_ec2.describe_subnets.return_value = {
            'Subnets': [{'DefaultForAz': False}]
        }
        
        # Mock no network interfaces
        mock_ec2.describe_network_interfaces.return_value = {
            'NetworkInterfaces': []
        }
        
        # Mock no instances
        mock_ec2.describe_instances.return_value = {
            'Reservations': []
        }
        
        result = self.subnet_resource.can_delete()
        
        self.assertTrue(result)
    
    @patch('aws_swiffer.resources.vpc.SubnetResource.get_client')
    def test_remove_success(self, mock_get_client):
        """Test successful subnet removal."""
        mock_ec2 = Mock()
        mock_get_client.return_value = mock_ec2
        
        # Mock can_delete returns True
        with patch.object(self.subnet_resource, 'can_delete', return_value=True), \
             patch.object(self.subnet_resource, '_should_proceed', return_value=True):
            
            context = ExecutionContext(dry_run=False, auto_approve=True)
            self.subnet_resource.remove(context)
            
            mock_ec2.delete_subnet.assert_called_once_with(SubnetId="subnet-12345678")
    
    @patch('aws_swiffer.resources.vpc.SubnetResource.get_client')
    def test_remove_dry_run(self, mock_get_client):
        """Test subnet removal in dry-run mode."""
        mock_ec2 = Mock()
        mock_get_client.return_value = mock_ec2
        
        # Mock can_delete returns True
        with patch.object(self.subnet_resource, 'can_delete', return_value=True), \
             patch.object(self.subnet_resource, '_should_proceed', return_value=True):
            
            context = ExecutionContext(dry_run=True, auto_approve=True)
            self.subnet_resource.remove(context)
            
            # Should not call delete_subnet in dry-run mode
            mock_ec2.delete_subnet.assert_not_called()
    
    @patch('aws_swiffer.resources.vpc.SubnetResource.get_client')
    def test_remove_cannot_delete(self, mock_get_client):
        """Test subnet removal when cannot delete."""
        mock_ec2 = Mock()
        mock_get_client.return_value = mock_ec2
        
        # Mock can_delete returns False
        with patch.object(self.subnet_resource, 'can_delete', return_value=False):
            
            context = ExecutionContext(dry_run=False, auto_approve=True)
            self.subnet_resource.remove(context)
            
            # Should not call delete_subnet when cannot delete
            mock_ec2.delete_subnet.assert_not_called()
    
    def test_string_representations(self):
        """Test string representations of subnet resource."""
        str_repr = str(self.subnet_resource)
        self.assertEqual(str_repr, "Subnet:test-subnet(subnet-12345678)")
        
        repr_str = repr(self.subnet_resource)
        expected = ("SubnetResource(subnet_id=subnet-12345678, name=test-subnet, "
                   "vpc_id=vpc-12345678, az=us-east-1a, cidr=10.0.1.0/24)")
        self.assertEqual(repr_str, expected)


if __name__ == '__main__':
    unittest.main()