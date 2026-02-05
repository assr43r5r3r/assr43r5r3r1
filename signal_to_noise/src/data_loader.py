"""
Data Loader for loading game data from JSON files.

Handles loading of nodes, links, messages, and scenarios.
"""

import json
import os
from typing import List, Dict, Any, Optional
from .settings import get_settings


class DataLoader:
    """
    Loads game data from JSON files.
    
    Handles:
    - Network nodes (nodes.json)
    - Network links (links.json)
    - Message templates (messages/)
    - Scenario files (scenarios/)
    """
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the data loader.
        
        Args:
            data_path: Path to data directory. Uses settings default if not specified.
        """
        self.settings = get_settings()
        self.data_path = data_path or self.settings.DATA_PATH
    
    def _load_json(self, filepath: str) -> Optional[Any]:
        """Load and parse a JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Data file not found: {filepath}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON parse error in {filepath}: {e}")
            return None
    
    def load_nodes(self, filename: str = "nodes.json") -> List[Dict[str, Any]]:
        """
        Load network nodes from JSON.
        
        Args:
            filename: Name of the nodes file
            
        Returns:
            List of node dictionaries
        """
        filepath = os.path.join(self.data_path, filename)
        data = self._load_json(filepath)
        
        if data is None:
            # Return default nodes for demo
            return self._get_default_nodes()
        
        return data if isinstance(data, list) else []
    
    def load_links(self, filename: str = "links.json") -> List[Dict[str, Any]]:
        """
        Load network links from JSON.
        
        Args:
            filename: Name of the links file
            
        Returns:
            List of link dictionaries
        """
        filepath = os.path.join(self.data_path, filename)
        data = self._load_json(filepath)
        
        if data is None:
            # Return default links for demo
            return self._get_default_links()
        
        return data if isinstance(data, list) else []
    
    def load_messages(self, filename: str = None) -> List[Dict[str, Any]]:
        """
        Load message templates from JSON.
        
        Args:
            filename: Specific message file, or None to load all from messages/
            
        Returns:
            List of message dictionaries
        """
        messages = []
        messages_dir = os.path.join(self.data_path, "messages")
        
        if filename:
            filepath = os.path.join(messages_dir, filename)
            data = self._load_json(filepath)
            if data:
                if isinstance(data, list):
                    messages.extend(data)
                elif isinstance(data, dict):
                    messages.append(data)
        else:
            # Load all message files
            if os.path.exists(messages_dir):
                for fname in os.listdir(messages_dir):
                    if fname.endswith('.json'):
                        filepath = os.path.join(messages_dir, fname)
                        data = self._load_json(filepath)
                        if data:
                            if isinstance(data, list):
                                messages.extend(data)
                            elif isinstance(data, dict):
                                messages.append(data)
        
        return messages
    
    def load_scenario(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """
        Load a scenario file.
        
        Args:
            scenario_name: Name of scenario (without .json extension)
            
        Returns:
            Scenario dictionary or None
        """
        filepath = os.path.join(self.data_path, "scenarios", f"{scenario_name}.json")
        return self._load_json(filepath)
    
    def load_strings(self, language: str = "en") -> Dict[str, str]:
        """
        Load localized strings.
        
        Args:
            language: Language code (e.g., 'en', 'es')
            
        Returns:
            Dictionary of string keys to localized values
        """
        filepath = os.path.join(self.data_path, "strings", f"{language}.json")
        data = self._load_json(filepath)
        return data if isinstance(data, dict) else {}
    
    def _get_default_nodes(self) -> List[Dict[str, Any]]:
        """Get default nodes for demo."""
        return [
            {"id": "A", "name": "Harbor", "x": 150, "y": 200, "capacity": 10240, "trust": 0.8, "owner": None, "type": "settlement"},
            {"id": "B", "name": "Market", "x": 350, "y": 150, "capacity": 8192, "trust": 0.7, "owner": "Market", "type": "hub"},
            {"id": "C", "name": "Outpost", "x": 300, "y": 350, "capacity": 6144, "trust": 0.6, "owner": None, "type": "relay"},
            {"id": "D", "name": "Medical", "x": 550, "y": 200, "capacity": 12288, "trust": 0.9, "owner": None, "type": "settlement"},
            {"id": "E", "name": "Militia HQ", "x": 500, "y": 400, "capacity": 8192, "trust": 0.5, "owner": "Militia", "type": "hub"},
            {"id": "F", "name": "Archive", "x": 700, "y": 300, "capacity": 16384, "trust": 0.95, "owner": "Archive", "type": "special"},
        ]
    
    def _get_default_links(self) -> List[Dict[str, Any]]:
        """Get default links for demo."""
        return [
            {"a": "A", "b": "B", "bandwidth": 2048, "latency": 0.1, "reliability": 0.95, "base_risk": 0.05},
            {"a": "A", "b": "C", "bandwidth": 1536, "latency": 0.15, "reliability": 0.85, "base_risk": 0.1},
            {"a": "B", "b": "C", "bandwidth": 2048, "latency": 0.12, "reliability": 0.9, "base_risk": 0.08},
            {"a": "B", "b": "D", "bandwidth": 3072, "latency": 0.08, "reliability": 0.95, "base_risk": 0.05},
            {"a": "C", "b": "E", "bandwidth": 1024, "latency": 0.2, "reliability": 0.75, "base_risk": 0.15},
            {"a": "D", "b": "E", "bandwidth": 1536, "latency": 0.15, "reliability": 0.8, "base_risk": 0.12},
            {"a": "D", "b": "F", "bandwidth": 4096, "latency": 0.05, "reliability": 0.98, "base_risk": 0.02},
            {"a": "E", "b": "F", "bandwidth": 2048, "latency": 0.1, "reliability": 0.85, "base_risk": 0.1},
        ]


def generate_message_id() -> str:
    """Generate a unique message ID."""
    import random
    import string
    return 'M' + ''.join(random.choices(string.digits, k=5))
