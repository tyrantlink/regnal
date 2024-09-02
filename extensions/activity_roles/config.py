from __future__ import annotations
from client.config.models import ConfigOption, ConfigSubcategory, OptionType, ConfigAttrs, AdditionalView, NewConfigSubcategory, NewConfigOption
from client.config.errors import ConfigValidationError
from .views import ActivityRolesIgnoreView
from discord import Member, Role
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import Client


async def validate_role(
    client: Client,
    option: ConfigOption,
    value: Role,
    user: Member
) -> tuple[Role, str | None]:
    if not value.is_assignable():
        raise ConfigValidationError(
            '''
            i can\'t assign that role!
            please make sure i have the manage roles permission and that the role is below my highest role
            '''.replace('    ', '').strip()
        )

    return value, None

subcategories = [
    NewConfigSubcategory(
        'guild',
        ConfigSubcategory(
            name='activity_roles',
            description='activity role options',
            additional_views=[
                AdditionalView(
                    required_permissions='activity_roles.ignore',
                    button_label='ignore roles',
                    button_row=2,
                    button_id='ignore_roles',
                    view=ActivityRolesIgnoreView
                )
            ]
        )
    )
]

options = [
    NewConfigOption(
        'guild',
        'activity_roles',
        ConfigOption(
            name='enabled',
            type=OptionType.BOOL,
            default=False,
            short_description='enable/disable activity roles',
            description='give your most active members a role'
        )
    ),
    NewConfigOption(
        'guild',
        'activity_roles',
        ConfigOption(
            name='role',
            type=OptionType.ROLE,
            default=None,
            attrs=ConfigAttrs(validation=validate_role),
            nullable=True,
            short_description='role given to active users',
            description='role given to active users'
        )
    ),
    NewConfigOption(
        'guild',
        'activity_roles',
        ConfigOption(
            name='timeframe',
            type=OptionType.INT,
            default=7,
            attrs=ConfigAttrs(min_value=1, max_value=30),
            short_description='number of days counted for activity',
            description='''
                number of days counted for activity
                (e.g. last 7 days)
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'guild',
        'activity_roles',
        ConfigOption(
            name='max_roles',
            type=OptionType.INT,
            default=10,
            attrs=ConfigAttrs(min_value=1, max_value=50),
            short_description='maximum number of roles to give',
            description='''
                maximum number of roles to give
                (e.g. the 10 most active members get a role)
            '''.replace('    ', '').strip()
        )
    ),
    NewConfigOption(
        'guild',
        'logging',
        ConfigOption(
            name='activity_roles',
            type=OptionType.BOOL,
            default=True,
            short_description='enable/disable logging of activity role changes',
            description='enable/disable logging of activity role changes'
        )
    )
]
