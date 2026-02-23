from typer import Typer
from aws_swiffer.factory.cloudfront.DistributionFactory import DistributionFactory
from aws_swiffer.utils import get_logger, get_tags, callback_check_account

logger = get_logger('Cloudfront')


def callback(profile: str = None, region: str = 'us-east-1', skip_account_check: bool = False):
    """
    Clean Cloudfront resources
    """
    callback_check_account(profile=profile, region=region, skip_account_check=skip_account_check)


cloudfront_command = Typer(callback=callback)


@cloudfront_command.command()
def remove_distribution_by_tags(tags: str = None):
    tags = get_tags(tags)
    logger.info(f"Search Distributions repositories by tags: \n{tags}")
    cloudfront_distributions = DistributionFactory().create_by_tags(tags=tags)
    logger.info(f"Found {len(cloudfront_distributions)} cloudfront distributions")
    for d in cloudfront_distributions:
        d.remove()


@cloudfront_command.command()
def remove_distribution_by_name(name: str):
    distribution = DistributionFactory().create_by_name(name=name)
    distribution.remove()

@cloudfront_command.command()
def remove_distribution_by_arn(arn: str):
    distribution = DistributionFactory().create_by_arn(arn=arn)
    distribution.remove()

@cloudfront_command.command()
def remove_distribution_by_id(id: str):
    distribution = DistributionFactory().create_by_name(name=id)
    distribution.remove()
