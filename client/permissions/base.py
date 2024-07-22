from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import PermissionHandler


def register_permissions(ph: 'PermissionHandler') -> None:
    ph.register_permission('admin.manage_permissions')
