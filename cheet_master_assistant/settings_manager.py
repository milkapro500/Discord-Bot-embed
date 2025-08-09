import json
import os
from typing import List, Dict, Set

class SettingsManager:
    """Manages bot settings including role permissions"""
    
    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = settings_file
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict:
        """Load settings from file or create default settings"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Default settings
        return {
            "allowed_roles": {},  # guild_id: [role_id1, role_id2, ...]
            "version": "1.0"
        }
    
    def _save_settings(self) -> None:
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving settings: {e}")
    
    def add_allowed_role(self, guild_id: int, role_id: int) -> bool:
        """Add a role to the allowed roles list for a guild"""
        guild_str = str(guild_id)
        
        if guild_str not in self.settings["allowed_roles"]:
            self.settings["allowed_roles"][guild_str] = []
        
        if role_id not in self.settings["allowed_roles"][guild_str]:
            self.settings["allowed_roles"][guild_str].append(role_id)
            self._save_settings()
            return True
        
        return False  # Role already exists
    
    def remove_allowed_role(self, guild_id: int, role_id: int) -> bool:
        """Remove a role from the allowed roles list for a guild"""
        guild_str = str(guild_id)
        
        if guild_str in self.settings["allowed_roles"]:
            if role_id in self.settings["allowed_roles"][guild_str]:
                self.settings["allowed_roles"][guild_str].remove(role_id)
                self._save_settings()
                return True
        
        return False  # Role not found
    
    def get_allowed_roles(self, guild_id: int) -> List[int]:
        """Get list of allowed role IDs for a guild"""
        guild_str = str(guild_id)
        return self.settings["allowed_roles"].get(guild_str, [])
    
    def is_user_allowed(self, guild_id: int, user_roles: List[int]) -> bool:
        """Check if user has any of the allowed roles"""
        allowed_roles = self.get_allowed_roles(guild_id)
        
        # If no roles are configured, allow everyone
        if not allowed_roles:
            return True
        
        # Check if user has any of the allowed roles
        return any(role_id in allowed_roles for role_id in user_roles)
    
    def clear_guild_settings(self, guild_id: int) -> bool:
        """Clear all settings for a guild"""
        guild_str = str(guild_id)
        
        if guild_str in self.settings["allowed_roles"]:
            del self.settings["allowed_roles"][guild_str]
            self._save_settings()
            return True
        
        return False

