from typer import Typer

from aws_swiffer.command import s3_command, codebuild_command, codepipeline_command, ec2_command, ecr_command, \
    ecs_command, iam_command
from aws_swiffer.utils import get_logger, callback_base

logger = get_logger("MAIN")

app = Typer(no_args_is_help=True, callback=callback_base)

# Add commands here
app.add_typer(codebuild_command, name="codebuild", no_args_is_help=True)
app.add_typer(codepipeline_command, name="codepipeline", no_args_is_help=True)
app.add_typer(ec2_command, name="ec2", no_args_is_help=True)
app.add_typer(ecr_command, name="ecr", no_args_is_help=True)
app.add_typer(ecs_command, name="ecs", no_args_is_help=True)
app.add_typer(iam_command, name="iam", no_args_is_help=True)
app.add_typer(s3_command, name="s3", no_args_is_help=True)

if __name__ == "__main__":
    app()
