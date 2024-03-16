if not 'TYPE_HINT': from . import PermissionHandler

def register_permissions(ph:'PermissionHandler') -> None:
	ph.register_permission('admin.manage_permissions')