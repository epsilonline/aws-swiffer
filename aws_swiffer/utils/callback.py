import os

from aws_swiffer.utils import get_logger, get_account_info, no_yes_dialog

logger = get_logger("AWS")


def callback_base(profile: str = None, region: str = 'eu-west-1', skip_account_check: bool = False):
    """
    Powerful cli for remove AWS resources! Powered by Epsilon Team.
    """
    # Use environment variable for configure aws sdk without pass configuration
    if region and not os.getenv('AWS_REGION'):
        os.environ['AWS_REGION'] = region
    if profile and not os.getenv('AWS_PROFILE'):
        os.environ['AWS_PROFILE'] = profile
    if skip_account_check:
        os.environ['SKIP_ACCOUNT_CHECK'] = str(skip_account_check)


def callback_check_account(profile: str = None, region: str = 'eu-west-1', skip_account_check: bool = False):
    callback_base(profile, region, skip_account_check)
    confirm_account()


def confirm_account():
    if os.getenv('SKIP_ACCOUNT_CHECK', 'false').lower() == 'true':
        return
    else:
        try:
            logger.info("Retrieve account information")
            account_info = get_account_info()
            continue_execution = (no_yes_dialog(title="Confirm account ID",
                                                text=f"You start operations in account \"{account_info['Account']}\" "
                                                     f"with aliases \"{', '.join(account_info['AccountAliases'])}\" "
                                                     f"and region \"{account_info['region']}\", "
                                                     f"continue?").run())
        except Exception as e:
            logger.error(e)
            logger.error("Cannot retrieve account information, check aws configuration")
            exit(-1)
    if not continue_execution:
        logger.error("Action aborted!")
        exit(-1)
