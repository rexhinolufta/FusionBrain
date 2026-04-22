"""
Memory Manager for FusionBrain/Jarvis
Handles persistent memory storage in JSON format
"""

import json
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, memory_file="memory.json", tasks_file="tasks.json"):
        self.memory_file = memory_file
        self.tasks_file = tasks_file
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize memory and tasks files if they don't exist."""
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w') as f:
                json.dump({
                    "owner": "Rexhino Lufta",
                    "preferences": {},
                    "facts": {},
                    "created_at": datetime.now().isoformat()
                }, f, indent=2)
        
        if not os.path.exists(self.tasks_file):
            with open(self.tasks_file, 'w') as f:
                json.dump([], f, indent=2)
    
    # ===== MEMORY OPERATIONS =====
    
    def load_memory(self):
        """Load all memories from file."""
        try:
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading memory: {str(e)}")
            return {}
    
    def save_memory(self, memory):
        """Save memories to file."""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(memory, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving memory: {str(e)}")
            return False
    
    def remember_fact(self, key, value):
        """Remember a fact."""
        memory = self.load_memory()
        if "facts" not in memory:
            memory["facts"] = {}
        memory["facts"][key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self.save_memory(memory)
        return f"I will remember that {key} is {value}."
    
    def recall_fact(self, key):
        """Recall a fact."""
        memory = self.load_memory()
        facts = memory.get("facts", {})
        if key in facts:
            return facts[key]["value"]
        return f"I don't remember anything about {key}."
    
    def get_all_facts(self):
        """Get all stored facts."""
        memory = self.load_memory()
        return memory.get("facts", {})
    
    def set_preference(self, key, value):
        """Set a preference."""
        memory = self.load_memory()
        if "preferences" not in memory:
            memory["preferences"] = {}
        memory["preferences"][key] = value
        self.save_memory(memory)
        return f"Preference '{key}' set to '{value}'."
    
    def get_preference(self, key, default=None):
        """Get a preference."""
        memory = self.load_memory()
        preferences = memory.get("preferences", {})
        return preferences.get(key, default)
    
    def get_owner_info(self):
        """Get owner information."""
        memory = self.load_memory()
        return {
            "owner": memory.get("owner", "Owner"),
            "preferences": memory.get("preferences", {}),
            "facts_count": len(memory.get("facts", {}))
        }
    
    # ===== TASK OPERATIONS =====
    
    def load_tasks(self):
        """Load all tasks from file."""
        try:
            with open(self.tasks_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading tasks: {str(e)}")
            return []
    
    def save_tasks(self, tasks):
        """Save tasks to file."""
        try:
            with open(self.tasks_file, 'w') as f:
                json.dump(tasks, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving tasks: {str(e)}")
            return False
    
    def add_task(self, title, description="", priority="medium", due_date=None):
        """Add a new task."""
        tasks = self.load_tasks()
        new_task = {
            "id": len(tasks) + 1,
            "title": title,
            "description": description,
            "priority": priority,
            "status": "pending",
            "due_date": due_date,
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }
        tasks.append(new_task)
        self.save_tasks(tasks)
        return f"Task '{title}' added successfully."
    
    def list_tasks(self, status="all"):
        """List tasks by status."""
        tasks = self.load_tasks()
        if status == "all":
            filtered_tasks = tasks
        else:
            filtered_tasks = [t for t in tasks if t["status"] == status]
        
        if not filtered_tasks:
            return f"No {status} tasks."
        
        task_list = f"Your {status} tasks:\n"
        for task in filtered_tasks:
            status_icon = "✓" if task["status"] == "completed" else "○"
            task_list += f"{status_icon} [{task['id']}] {task['title']} (Priority: {task['priority']})\n"
        
        return task_list
    
    def complete_task(self, task_id):
        """Mark a task as completed."""
        tasks = self.load_tasks()
        for task in tasks:
            if task["id"] == task_id:
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                self.save_tasks(tasks)
                return f"Task {task_id} '{task['title']}' marked as completed."
        return f"Task {task_id} not found."
    
    def update_task(self, task_id, **kwargs):
        """Update task details."""
        tasks = self.load_tasks()
        for task in tasks:
            if task["id"] == task_id:
                for key, value in kwargs.items():
                    if key in task:
                        task[key] = value
                self.save_tasks(tasks)
                return f"Task {task_id} updated successfully."
        return f"Task {task_id} not found."
    
    def delete_task(self, task_id):
        """Delete a task."""
        tasks = self.load_tasks()
        tasks = [t for t in tasks if t["id"] != task_id]
        self.save_tasks(tasks)
        return f"Task {task_id} deleted."
    
    def get_pending_tasks(self):
        """Get all pending tasks."""
        tasks = self.load_tasks()
        return [t for t in tasks if t["status"] != "completed"]
    
    def get_task_stats(self):
        """Get task statistics."""
        tasks = self.load_tasks()
        total = len(tasks)
        completed = len([t for t in tasks if t["status"] == "completed"])
        pending = total - completed
        
        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "completion_rate": f"{(completed/total*100):.1f}%" if total > 0 else "0%"
        }
    
    # ===== DAILY BRIEFING =====
    
    def daily_briefing(self):
        """Generate daily briefing."""
        briefing = "Good morning! ☀️\n"
        briefing += f"Current time: {datetime.now().strftime('%H:%M, %A')}\n\n"
        
        # Add pending tasks
        pending_tasks = self.get_pending_tasks()
        if pending_tasks:
            briefing += f"📋 You have {len(pending_tasks)} pending tasks:\n"
            for task in pending_tasks[:5]:  # Show top 5
                briefing += f"  • {task['title']} (Priority: {task['priority']})\n"
        else:
            briefing += "✓ You have no pending tasks!\n"
        
        # Add owner info
        owner_info = self.get_owner_info()
        briefing += f"\n👤 Owner: {owner_info['owner']}\n"
        briefing += f"📚 Stored facts: {owner_info['facts_count']}\n"
        
        # Add task stats
        stats = self.get_task_stats()
        briefing += f"\n📊 Task Statistics:\n"
        briefing += f"  • Total: {stats['total']}\n"
        briefing += f"  • Completed: {stats['completed']}\n"
        briefing += f"  • Pending: {stats['pending']}\n"
        briefing += f"  • Completion Rate: {stats['completion_rate']}\n"
        
        return briefing
