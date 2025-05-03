from rest_framework.routers import DefaultRouter
import re


class KebabCaseRouter(DefaultRouter):
    """
    Custom router that uses kebab-case instead of snake_case in URLs
    """
    def get_urls(self):
        """
        Uses kebab-case for API URLs
        """
        urls = super().get_urls()
        
        # Simpler and safer version to convert URLs to kebab-case
        for pattern in urls:
            if hasattr(pattern, 'pattern') and hasattr(pattern.pattern, '_regex'):
                # This is a safer pattern: convert only words with underscore
                # avoiding named parameters and keeping balanced parentheses
                old_regex = pattern.pattern._regex
                
                # Converts only words with underscore to kebab-case, keeping the groups intact
                # This function replaces only underscores that are not inside named groups (?P<n>)
                def replace_safe(match):
                    # If it's a named group, keep it as is
                    if match.group(1):
                        return match.group(0)
                    # Otherwise, replace underscore with hyphen
                    return match.group(0).replace('_', '-')
                
                # Uses regex to identify and preserve named groups, replacing only
                # underscores in other parts of the pattern
                new_regex = re.sub(
                    r'(\(\?P<[^>]+>)|([a-zA-Z0-9_]+)',
                    replace_safe,
                    old_regex
                )
                
                pattern.pattern._regex = new_regex
        
        return urls


# Router instances will be created in specific apps 