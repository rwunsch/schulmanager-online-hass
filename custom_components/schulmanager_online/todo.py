"""Todo platform for Schulmanager Online homework lists."""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity
from homeassistant.components.todo.const import TodoListEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SchulmanagerDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _make_homework_uid(student_id: int, item: Dict[str, Any]) -> str:
    """Generate unique ID for homework item using MD5."""
    date = item.get("date", "")
    subject = item.get("subject", "") or ""
    homework = item.get("homework", "") or item.get("description", "") or ""
    key = f"{student_id}_{date}_{subject}_{homework}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Schulmanager Online todo list entities."""
    _LOGGER.debug("Setting up Schulmanager todo entities")
    
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    students = hass.data[DOMAIN][config_entry.entry_id]["students"]
    
    entities: List[TodoListEntity] = []
    
    for student in students:
        student_id = student.get("id")
        if not student_id:
            continue
        
        _LOGGER.debug("Creating homework todo entity for student ID: %s", student_id)
        entities.append(
            HomeworkTodoList(
                coordinator=coordinator,
                student_id=student_id,
                student_info=student,
            )
        )
    
    _LOGGER.debug("Adding %d todo entities", len(entities))
    async_add_entities(entities, update_before_add=True)


class HomeworkTodoList(CoordinatorEntity[SchulmanagerDataUpdateCoordinator], TodoListEntity):
    """Todo list entity for student homework."""
    
    _attr_has_entity_name = True
    _attr_supported_features = TodoListEntityFeature.UPDATE_TODO_ITEM
    _attr_icon = "mdi:clipboard-check-multiple-outline"
    
    def __init__(
        self,
        coordinator: SchulmanagerDataUpdateCoordinator,
        student_id: int,
        student_info: Dict[str, Any],
    ) -> None:
        """Initialize a homework todo list entity for a student."""
        super().__init__(coordinator)
        self.student_id = student_id
        self.student_info = student_info
        self._attr_unique_id = f"schulmanager_homework_todo_{student_id}"
        self._attr_name = "Homework"
        self._attr_todo_items: Optional[List[TodoItem]] = None
        
        _LOGGER.info(
            "Created HomeworkTodoList for student ID %s (unique_id: %s)",
            student_id,
            self._attr_unique_id,
        )
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        student_name = f"{self.student_info.get('firstname', '')} {self.student_info.get('lastname', '')}"
        return DeviceInfo(
            identifiers={(DOMAIN, str(self.student_id))},
            name=f"Schulmanager - {student_name}",
            manufacturer="Schulmanager Online",
            model="Student Schedule",
        )
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        student_data = self.coordinator.get_student_data(self.student_id)
        if not student_data:
            self._attr_todo_items = []
            super()._handle_coordinator_update()
            return
        
        homework_data = student_data.get("homework", {}) or {}
        homeworks = homework_data.get("homeworks", []) or []
        
        _LOGGER.debug(
            "Updating homework items for student %s: found %d items",
            self.student_id,
            len(homeworks),
        )
        
        # Create a map of existing items by UID for status preservation
        existing_items: Dict[str, TodoItem] = {}
        if self._attr_todo_items:
            existing_items = {
                item.uid: item
                for item in self._attr_todo_items
                if item.uid
            }
        
        if not homeworks:
            self._attr_todo_items = []
        else:
            todo_items: List[TodoItem] = []
            current_uids = set()
            
            for item in homeworks:
                uid = _make_homework_uid(self.student_id, item)
                current_uids.add(uid)
                
                # Build title from subject and homework
                subject = (item.get("subject") or "").strip()
                homework = (item.get("homework") or item.get("description") or "").strip()
                date = (item.get("date") or "").strip()
                
                # Create title with various fallback formats
                if subject and homework:
                    if date:
                        title = f"[{date}] {subject}: {homework}"
                    else:
                        title = f"{subject}: {homework}"
                elif homework:
                    title = homework
                elif subject:
                    title = f"{subject}: (Homework)"
                else:
                    title = "Homework"
                
                # Limit title length
                title = title[:255]
                
                # Preserve existing status if item already exists
                existing_item = existing_items.get(uid)
                status = (
                    existing_item.status
                    if existing_item
                    else TodoItemStatus.NEEDS_ACTION
                )
                
                todo_items.append(
                    TodoItem(
                        summary=title,
                        uid=uid,
                        status=status,
                    )
                )
                
                if existing_item:
                    _LOGGER.debug(
                        "Preserved status for TodoItem: %s (uid: %s, status: %s)",
                        title[:50],
                        uid[:8],
                        status,
                    )
                else:
                    _LOGGER.debug(
                        "Created new TodoItem: %s (uid: %s)",
                        title[:50],
                        uid[:8],
                    )
            
            # Log removed items for debugging
            if existing_items:
                removed_uids = set(existing_items.keys()) - current_uids
                if removed_uids:
                    _LOGGER.debug(
                        "Removed %d outdated todo items for student %s: %s",
                        len(removed_uids),
                        self.student_id,
                        [uid[:8] for uid in removed_uids],
                    )
            
            self._attr_todo_items = todo_items
        
        _LOGGER.debug(
            "Updated %d todo items for student %s",
            len(self._attr_todo_items or []),
            self.student_id,
        )
        super()._handle_coordinator_update()
    
    async def async_create_todo_item(self, item: TodoItem) -> None:
        """Create a new todo item."""
        raise NotImplementedError(
            "Cannot create items in a homework list from Schulmanager Online"
        )
    
    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update an existing todo item (status changes only)."""
        if not item.uid or not self._attr_todo_items:
            return
        
        # Find and update the item in our local list
        for i, existing_item in enumerate(self._attr_todo_items):
            if existing_item.uid == item.uid:
                # Only allow status updates, preserve other fields from original
                updated_item = TodoItem(
                    summary=existing_item.summary,
                    uid=existing_item.uid,
                    status=item.status or existing_item.status,
                    due=existing_item.due,
                    description=existing_item.description,
                )
                self._attr_todo_items[i] = updated_item
                
                _LOGGER.debug(
                    "Updated TodoItem status: %s (uid: %s, status: %s)",
                    (existing_item.summary or "")[:50],
                    (item.uid or "unknown")[:8],
                    updated_item.status,
                )
                
                # Notify Home Assistant of the state change
                self.async_write_ha_state()
                return
        
        _LOGGER.warning(
            "TodoItem with uid %s not found for update",
            (item.uid or "unknown")[:8],
        )
    
    async def async_delete_todo_items(self, uids: List[str]) -> None:
        """Delete todo items."""
        raise NotImplementedError(
            "Cannot delete homework items from Schulmanager Online"
        )
    
    @property
    def should_poll(self) -> bool:
        """No polling needed, coordinator handles updates."""
        return False

