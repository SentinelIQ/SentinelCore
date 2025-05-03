import sys
import importlib
import pkgutil
from django.core.management.base import BaseCommand
from django.urls import get_resolver
from django.contrib.auth import get_user_model
from django.apps import apps
from auth_app.permission_matrix import ROLE_PERMISSIONS, has_permission, get_required_permission
from api.core.rbac import HasEntityPermission
import inspect
from rest_framework import viewsets

User = get_user_model()


class Command(BaseCommand):
    help = "Validates the RBAC permission setup across the entire application"

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically fix common RBAC issues',
        )
        
    def handle(self, *args, **options):
        fix_issues = options.get('fix', False)
        self.stdout.write(self.style.NOTICE("Starting RBAC validation..."))
        
        # Validate role constants
        roles_from_user = [choice[0] for choice in User.Role.choices]
        roles_from_matrix = list(ROLE_PERMISSIONS.keys())
        
        # Check for missing roles in matrix
        missing_roles = [role for role in roles_from_user if role not in roles_from_matrix]
        if missing_roles:
            self.stdout.write(self.style.ERROR(
                f"ERROR: The following roles are defined in User model but missing in permission matrix: {missing_roles}"
            ))
        
        # Check for extra roles in matrix
        extra_roles = [role for role in roles_from_matrix if role not in roles_from_user]
        if extra_roles:
            self.stdout.write(self.style.WARNING(
                f"WARNING: The following roles are defined in permission matrix but not in User model: {extra_roles}"
            ))
        
        # Scan for views using permissions
        self.stdout.write(self.style.NOTICE("Scanning for views..."))
        
        # Import all modules from installed apps
        self._import_app_modules()
        
        # Force import known modules with ViewSets
        self._force_import_known_viewsets()
        
        viewset_count = 0
        rbac_viewset_count = 0
        entity_type_missing = []
        
        # List all discovered ViewSets
        discovered_viewsets = []
        
        # Find all ViewSet classes
        for module_name in list(sys.modules.keys()):
            try:
                module = sys.modules[module_name]
                if not module or not hasattr(module, '__name__'):
                    continue
                    
                # Only check our own project modules
                if not any(module.__name__.startswith(app_config.name) for app_config in apps.get_app_configs()):
                    continue
                    
                for name, obj in inspect.getmembers(module):
                    # Check if it's a ViewSet class (but not the base classes themselves)
                    if (inspect.isclass(obj) and 
                        issubclass(obj, viewsets.ViewSet) and 
                        obj not in [viewsets.ViewSet, viewsets.GenericViewSet, viewsets.ModelViewSet, viewsets.ReadOnlyModelViewSet]):
                        
                        # Skip abstract base classes or mixins
                        if 'Mixin' in obj.__name__ or obj.__name__.startswith('Abstract'):
                            continue
                            
                        viewset_count += 1
                        discovered_viewsets.append(f"{obj.__name__} in {module.__name__}")
                        self.stdout.write(f"Found ViewSet: {obj.__name__} in {module.__name__}")
                        
                        # Check if it uses HasEntityPermission
                        uses_rbac = False
                        for perm_class in getattr(obj, 'permission_classes', []):
                            # Check if the permission class is HasEntityPermission or a subclass of it
                            try:
                                if perm_class == HasEntityPermission:
                                    uses_rbac = True
                                    rbac_viewset_count += 1
                                    break
                                elif inspect.isclass(perm_class):
                                    for base in inspect.getmro(perm_class):
                                        if base == HasEntityPermission:
                                            uses_rbac = True
                                            rbac_viewset_count += 1
                                            break
                                    if uses_rbac:
                                        break
                            except (TypeError, Exception) as e:
                                self.stdout.write(f"Error checking permission class {perm_class}: {str(e)}")
                                continue
                        
                        # Check for entity_type if using RBAC
                        if uses_rbac and not hasattr(obj, 'entity_type') and not hasattr(obj, 'queryset'):
                            entity_type_missing.append(f"{obj.__name__} in {module.__name__}")
            except (ImportError, AttributeError, TypeError) as e:
                # Just continue if there's an error with a module
                pass
                
        self.stdout.write(self.style.SUCCESS(f"Found {viewset_count} ViewSets, {rbac_viewset_count} using RBAC"))
        
        if discovered_viewsets:
            self.stdout.write("Discovered ViewSets:")
            for vs in discovered_viewsets:
                self.stdout.write(f"  - {vs}")
                
        if entity_type_missing:
            self.stdout.write(self.style.WARNING(
                f"WARNING: The following ViewSets are using RBAC but missing entity_type: {entity_type_missing}"
            ))
            
        # Check for permission inconsistencies
        self.stdout.write(self.style.NOTICE("Validating permission hierarchies..."))
        issue_count = 0
        
        # Check that admin_company has all permissions of analyst_company and read_only
        for permission in ROLE_PERMISSIONS.get('analyst_company', []):
            if permission not in ROLE_PERMISSIONS.get('admin_company', []):
                issue_count += 1
                self.stdout.write(self.style.ERROR(
                    f"ERROR: Permission '{permission}' granted to analyst_company but not to admin_company"
                ))
                
        for permission in ROLE_PERMISSIONS.get('read_only', []):
            if permission not in ROLE_PERMISSIONS.get('admin_company', []):
                issue_count += 1
                self.stdout.write(self.style.ERROR(
                    f"ERROR: Permission '{permission}' granted to read_only but not to admin_company"
                ))
            if permission not in ROLE_PERMISSIONS.get('analyst_company', []):
                issue_count += 1
                self.stdout.write(self.style.ERROR(
                    f"ERROR: Permission '{permission}' granted to read_only but not to analyst_company"
                ))
                
        # Report summary
        if issue_count == 0:
            self.stdout.write(self.style.SUCCESS("RBAC validation completed successfully with no issues!"))
        else:
            self.stdout.write(self.style.ERROR(f"RBAC validation completed with {issue_count} issues"))
            
        return None
        
    def _import_app_modules(self):
        """
        Dynamically import all modules from installed apps to ensure 
        ViewSets are loaded into the Python environment
        """
        self.stdout.write("Importing app modules...")
        app_configs = apps.get_app_configs()
        
        # Import key modules where ViewSets are likely to be defined
        view_module_patterns = ['views', 'viewsets', 'api.v1', 'api.views']
        
        for app_config in app_configs:
            self.stdout.write(f"Checking app: {app_config.name}")
            
            # Skip Django's built-in apps
            if app_config.name.startswith('django.'):
                continue
                
            # Import the app module itself
            try:
                importlib.import_module(app_config.name)
                self.stdout.write(f"Imported app module: {app_config.name}")
            except ImportError:
                pass
                
            # Try to import common view modules
            for pattern in view_module_patterns:
                try:
                    module_path = f"{app_config.name}.{pattern}"
                    importlib.import_module(module_path)
                    self.stdout.write(f"Imported module: {module_path}")
                except ImportError:
                    pass
                    
            # Try recursive import for all app submodules
            try:
                app_module = importlib.import_module(app_config.name)
                for _, name, is_pkg in pkgutil.iter_modules(app_module.__path__, app_module.__name__ + '.'):
                    try:
                        importlib.import_module(name)
                    except ImportError:
                        pass
            except (ImportError, AttributeError):
                pass
                
    def _force_import_known_viewsets(self):
        """
        Explicitly import modules where we know ViewSets are defined based on code search
        """
        self.stdout.write("Forcing import of known ViewSet modules...")
        
        known_modules = [
            'companies.views',
            'auth_app.views',
            'api.v1.common.views',
            'api.v1.incidents.views',
            'api.v1.alerts.views',
            'api.v1.companies.views',
            'api.v1.auth.views',
            'api.v1.auth.views.user',
            # Include nested modules
            'api.v1.incidents.views.__init__',
            'api.v1.alerts.views.__init__',
            'api.v1.companies.views.__init__',
            'api.v1.auth.views.__init__'
        ]
        
        for module_name in known_modules:
            try:
                module = importlib.import_module(module_name)
                self.stdout.write(f"Successfully imported: {module_name}")
                
                # For __init__ modules, also try to import potential ViewSet modules
                if module_name.endswith('__init__'):
                    base_module = module_name.replace('.__init__', '')
                    # Try to import common patterns
                    for suffix in ['detail', 'list', 'create', 'custom_actions']:
                        full_module = f"{base_module}.{suffix}"
                        try:
                            importlib.import_module(full_module)
                            self.stdout.write(f"Successfully imported: {full_module}")
                        except ImportError:
                            pass
            except ImportError as e:
                self.stdout.write(f"Failed to import {module_name}: {str(e)}")
                pass 