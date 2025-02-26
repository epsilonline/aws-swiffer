import os

from typer import Typer

from aws_swiffer.command import s3_command, codebuild_command, codepipeline_command, ec2_command, ecr_command, \
    ecs_command, iam_command
from aws_swiffer.utils import get_account_info, no_yes_dialog, get_logger
import aws_swiffer.command as command

logger = get_logger("MAIN")


def callback(profile: str = None, region: str = 'eu-west-1', skip_account_check: bool = False):
    """
    Powerful cli for remove AWS resources! Powered by Epsilon Team.
    """
    # Use environment variable for configure aws sdk without pass configuration
    if region:
        os.environ['AWS_REGION'] = region
    if profile:
        os.environ['AWS_PROFILE'] = profile
    if os.getenv('SKIP_ACCOUNT_CHECK', 'false').lower() == 'true' or skip_account_check:
        return
    else:
        try:
            logger.info("Retrieve account information")
            account_info = get_account_info()
            continue_execution = (no_yes_dialog(title="Confirm account ID",
                                                text=f"You start operations in account \"{account_info['Account']}\" "
                                                     f"with aliases \"{', '.join(account_info['AccountAliases'])}\", "
                                                     f"continue?").run())
        except Exception:
            logger.error("Cannot retrieve account information, check aws configuration")
            exit(-1)
    if not continue_execution:
        logger.error("Action aborted!")
        exit(-1)


app = Typer(no_args_is_help=True)


# Add commands here
app.add_typer(codebuild_command, name="codebuild", no_args_is_help=True, callback=callback)
app.add_typer(codepipeline_command, name="codepipeline", no_args_is_help=True, callback=callback)
app.add_typer(ec2_command, name="ec2", no_args_is_help=True, callback=callback)
app.add_typer(ecr_command, name="ecr", no_args_is_help=True, callback=callback)
app.add_typer(ecs_command, name="ecs", no_args_is_help=True, callback=callback)
app.add_typer(iam_command, name="iam", no_args_is_help=True, callback=callback)
app.add_typer(s3_command, name="s3", no_args_is_help=True, callback=callback)

if __name__ == "__main__":
    app()
