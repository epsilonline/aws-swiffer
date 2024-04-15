import os

from typer import Typer
from aws_swiffer.utils import get_account_info, no_yes_dialog, get_logger
import aws_swiffer.command as command

logger = get_logger("MAIN")


def callback(profile: str = None, region: str = 'eu-west-1', skip_account_check: bool = False):
    """
    Powerful cli for remove AWS resources! Powered by Epsilon Team.
    """
    if region:
        os.environ['AWS_REGION'] = region
    if profile:
        os.environ['AWS_PROFILE'] = profile
    if os.getenv('SKIP_ACCOUNT_CHECK', 'false').lower() == 'true' or skip_account_check:
        return
    else:
        logger.info("Retrieve information account")
        account_info = get_account_info()
        continue_execution = (no_yes_dialog(title="Confirm account ID",
                                            text=f"You start operations in account \"{account_info['Account']}\" "
                                                 f"with aliases \"{', '.join(account_info['AccountAliases'])}\", "
                                                 f"continue?").run())
    if not continue_execution:
        logger.error("Action aborted!")
        exit(-1)


app = Typer(callback=callback, no_args_is_help=True)


# Add commands here
app.command()(command.remove_task_definitions_by_tags)
app.command()(command.remove_bucket_by_name)
app.command()(command.remove_iam_group_by_name)
app.command()(command.remove_iam_user_by_name)
app.command()(command.remove_iam_policy_by_tags)
app.command()(command.remove_iam_policy_by_name)
app.command()(command.remove_instance_by_id)
app.command()(command.remove_ecr_by_name)
app.command()(command.remove_ecr_by_tags)
app.command()(command.remove_service_by_arn)
app.command()(command.remove_service_by_tags)
app.command()(command.remove_service_by_arns)
app.command()(command.remove_ecs_cluster_by_tags)
app.command()(command.remove_codepipeline_by_tags)
app.command()(command.remove_codebuild_projects_by_tags)
app.command()(command.remove_codebuild_project_by_name)
app.command()(command.remove_bucket_by_tags)

if __name__ == "__main__":
    app()
