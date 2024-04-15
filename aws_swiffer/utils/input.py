import json

from prompt_toolkit import print_formatted_text, prompt
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.formatted_text import AnyFormattedText
# noinspection PyProtectedMember
from prompt_toolkit.shortcuts.dialogs import _create_app
from prompt_toolkit.styles import BaseStyle
from prompt_toolkit.widgets import (
    Button,
    Dialog,
    Label,
)


def no_yes_dialog(
    title: AnyFormattedText = "",
    text: AnyFormattedText = "",
    yes_text: str = "Yes",
    no_text: str = "No",
    style: BaseStyle | None = None,
) -> Application[bool]:
    """
    Display a Yes/No dialog.
    Return a boolean.
    """

    def yes_handler() -> None:
        get_app().exit(result=True)

    def no_handler() -> None:
        get_app().exit(result=False)

    dialog = Dialog(
        title=title,
        body=Label(text=text, dont_extend_height=True),
        buttons=[
            Button(text=no_text, handler=no_handler),
            Button(text=yes_text, handler=yes_handler),
        ],
        with_background=True,
    )

    return _create_app(dialog, style)


def prompt_input_tags() -> dict:
    get_input = True
    print_formatted_text('Insert tags.')
    print_formatted_text('Value is comma separated list.')
    print_formatted_text('For quit leave value blank and press enter')

    tags = {}

    while get_input:
        k = prompt("Key: ")
        if not k:
            return tags
        if k in tags:
            print_formatted_text("Tag key already taken, value are appended to existing")
        v = prompt("Value: ")
        if not v:
            return tags
        tags[k] = tags.get(k, []) + [value.strip() for value in v.split(',')]
        # new_inputs = yes_no_dialog(
        #     title='Add new tags',
        #     text='Do you want to confirm?').run()
        # if not new_inputs:
        #     return tags


def parse_input_tags(tags: str) -> dict:
    t = tags.replace('\'', '"')
    return json.loads(t)


def get_tags(tags: str = None) -> dict:
    if not tags:
        tags = prompt_input_tags()
    else:
        tags = parse_input_tags(tags)
    return tags


def ask_delete_confirm(resource_name: str) -> bool:
    choice = no_yes_dialog(
        title=f'Confirm deletion', text=f'Are sure to delete {resource_name}? All data will lost!',
    ).run()
    return choice
