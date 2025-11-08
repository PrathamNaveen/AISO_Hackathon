'''
The memory function for the agent.
Simple storage for user_id and preferences using LangGraph's InMemoryStore.
'''

from langgraph.store.memory import InMemoryStore
from typing import Optional


class AgentMemory:
    """Simple memory system using LangGraph's InMemoryStore."""
    
    def __init__(self):
        """Initialize the memory store."""
        self.store = InMemoryStore()
    
    def add_user(self, user_id: str, preferences_text: str):
        """
        Add or update a user's preferences.
        
        Args:
            user_id (str): Unique user identifier
            preferences_text (str): User preferences as text
            
        Example:
            memory.add_user("user123", "this user prefer KLM, night flight, budget from 100-1000, and economy class")
        """
        namespace = ("users", user_id)
        self.store.put(
            namespace=namespace,
            key="preferences",
            value={"user_id": user_id, "preferences_text": preferences_text}
        )
        print(f"✅ Saved preferences for user: {user_id}")
    
    def get_user(self, user_id: str) -> Optional[dict]:
        """
        Get a user's preferences.
        
        Args:
            user_id (str): User identifier
            
        Returns:
            dict: User data with user_id and preferences_text, or None if not found
        """
        namespace = ("users", user_id)
        try:
            result = self.store.get(namespace=namespace, key="preferences")
            if result:
                return result.value
        except:
            pass
        return None
    
    def update_preferences(self, user_id: str, preferences_text: str):
        """
        Update a user's preferences (alias for add_user).
        
        Args:
            user_id (str): User identifier
            preferences_text (str): New preferences text
        """
        self.add_user(user_id, preferences_text)
    
    def delete_user(self, user_id: str):
        """
        Delete a user from memory.
        
        Args:
            user_id (str): User identifier
        """
        namespace = ("users", user_id)
        self.store.delete(namespace=namespace, key="preferences")
        print(f"✅ Deleted user: {user_id}")
    
    def user_exists(self, user_id: str) -> bool:
        """Check if a user exists in memory."""
        return self.get_user(user_id) is not None
    
    def get_all_users(self) -> dict:
        """Get all users in memory."""
        # Search all users namespace
        try:
            results = self.store.search(("users",))
            users = {}
            for item in results:
                user_data = item.value
                users[user_data['user_id']] = user_data
            return users
        except:
            return {}


# Example usage
if __name__ == "__main__":
    print("🧠 Testing Simple Agent Memory with InMemoryStore\n")
    
    # Create memory instance
    memory = AgentMemory()
    
    # Add users
    print("➕ Adding users...")
    memory.add_user(
        "user123",
        "this user prefer KLM, night flight, budget from 100-1000, and economy class"
    )
    
    memory.add_user(
        "user456",
        "prefer Delta or Emirates, morning flights, budget 500-2000, business class"
    )
    
    memory.add_user(
        "user789",
        "prefer budget airlines, any time, budget 50-300, economy class, no luggage"
    )
    
    # Get user preferences
    print("\n📋 Retrieving user preferences:")
    user = memory.get_user("user123")
    if user:
        print(f"User ID: {user['user_id']}")
        print(f"Preferences: {user['preferences_text']}")
    
    # Check if user exists
    print(f"\n❓ Does user456 exist? {memory.user_exists('user456')}")
    print(f"❓ Does user999 exist? {memory.user_exists('user999')}")
    
    # Update preferences
    print("\n🔄 Updating user123 preferences...")
    memory.update_preferences(
        "user123",
        "this user prefer KLM or Lufthansa, any time, budget 200-1500, economy or premium economy"
    )
    
    # Show updated preferences
    user = memory.get_user("user123")
    if user:
        print(f"Updated preferences: {user['preferences_text']}")
    
    # Show all users
    print("\n📊 All users in memory:")
    all_users = memory.get_all_users()
    print(f"Total users: {len(all_users)}")
    for user_id, user_data in all_users.items():
        print(f"\n{user_id}:")
        print(f"  {user_data['preferences_text']}")
    
    # Delete a user
    print("\n🗑️ Deleting user789...")
    memory.delete_user("user789")
    print(f"Remaining users: {len(memory.get_all_users())}")
    
    print("\n✅ Memory test complete!")
