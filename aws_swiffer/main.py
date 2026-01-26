from typer import Typer, Option

from aws_swiffer.command import s3_command, codebuild_command, codepipeline_command, ec2_command, ecr_command, \
    ecs_command, iam_command
from aws_swiffer.command.dynamodb import dynamodb_command
from aws_swiffer.utils import get_logger, callback_base

logger = get_logger("MAIN")


def main_callback(
    profile: str = None,
    region: str = 'eu-west-1',
    skip_account_check: bool = False,
    dry_run: bool = Option(False, "--dry-run", help="Simulate operations without making actual changes"),
    auto_approve: bool = Option(False, "--auto-approve", help="Skip confirmation prompts (use with caution!)")
):
    """Powerful CLI for removing AWS resources! Powered by Epsilon Team."""
    callback_base(profile, region, skip_account_check, dry_run, auto_approve)


app = Typer(no_args_is_help=True, callback=main_callback)

# Add commands here
app.add_typer(codebuild_command, name="codebuild", no_args_is_help=True)
app.add_typer(codepipeline_command, name="codepipeline", no_args_is_help=True)
app.add_typer(ec2_command, name="ec2", no_args_is_help=True)
app.add_typer(ecr_command, name="ecr", no_args_is_help=True)
app.add_typer(ecs_command, name="ecs", no_args_is_help=True)
app.add_typer(iam_command, name="iam", no_args_is_help=True)
app.add_typer(s3_command, name="s3", no_args_is_help=True)
app.add_typer(dynamodb_command, name="dynamodb", no_args_is_help=True)

if __name__ == "__main__":
    app()
