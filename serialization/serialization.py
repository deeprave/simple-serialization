# -*- coding: utf-8 -*-
"""
Unified serialization utilities combining dataclass, object, and namespace serialization.

This module provides a comprehensive serialization framework that unifies the functionality
of dataclass serialization, rich object serialization, and namespace handling.
"""

from abc import ABC, abstractmethod
from dataclasses import is_dataclass, fields
from types import SimpleNamespace
from typing import Any, Dict
import json


__all__ = [
    "SerializationMixin",
    "DataclassSerializer",
    "ObjectSerializer",
    "Namespace",
    "SerializationEncoder",
    "serialize_object",
    "to_namespace",
]


class SerializationMixin(ABC):
    """Base mixin providing common serialization functionality."""

    @abstractmethod
    def serialize(self, **kwargs) -> Dict[str, Any]:
        """Serialize the object to a dictionary."""
        pass

    def to_dict(self, **kwargs) -> Dict[str, Any]:
        """Alias for serialize() returning a dict."""
        result = self.serialize(**kwargs)
        return dict(result) if hasattr(result, "items") else result

    def to_json(self, indent=None, **kwargs) -> str:
        """Serialize to JSON string."""
        return json.dumps(
            self.serialize(**kwargs), cls=SerializationEncoder, indent=indent
        )


class DataclassSerializer(SerializationMixin):
    """Enhanced dataclass serialization with field mapping and exclusions."""

    # Class-level configuration - override in subclasses
    _field_map: Dict[str, str] = {}  # field_name -> serialized_name
    _exclude_fields: set = set()  # fields to exclude
    _default_values: Dict[str, Any] = {}  # default values for missing fields

    def __init_subclass__(cls, **kwargs):
        """Initialize a subclass with empty configurations if not defined."""
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "_field_map"):
            cls._field_map = {}
        if not hasattr(cls, "_exclude_fields"):
            cls._exclude_fields = set()
        if not hasattr(cls, "_default_values"):
            cls._default_values = {}

    def serialize(self, nested=True, **kwargs) -> Dict[str, Any]:
        """Serialize dataclass with field mapping."""
        if not is_dataclass(self):
            raise ValueError("DataclassSerializer can only be used with dataclasses")

        result = {}
        for field in fields(self):
            if field.name in self._exclude_fields:
                continue

            # Get value with a custom transformer if available
            value = self._get_field_value(field.name)
            if value is None:
                continue

            # Handle nested serialization
            if hasattr(value, "serialize") and nested:
                value = value.serialize(nested=nested, **kwargs)
            elif is_dataclass(value) and nested:
                # Convert dataclass to dict recursively
                value = {
                    f.name: getattr(value, f.name)
                    for f in fields(value)
                    if getattr(value, f.name) is not None
                }
            elif isinstance(value, list) and nested:
                # Handle lists of serializable objects
                value = [
                    item.serialize(**kwargs) if hasattr(item, "serialize") else item
                    for item in value
                ]

            # Apply field name mapping
            key = self._field_map.get(field.name, field.name)
            result[key] = value

        return result

    def _get_field_value(self, field_name: str) -> Any:
        """Get field value, with support for custom value transformers."""
        # Check for custom value transformer method
        transformer_name = f"value_of_{field_name}"
        if hasattr(self, transformer_name):
            transformer = getattr(self, transformer_name)
            if callable(transformer):
                raw_value = getattr(
                    self, field_name, self._default_values.get(field_name)
                )
                return transformer(raw_value)

        return getattr(self, field_name, self._default_values.get(field_name))


class ObjectSerializer(SerializationMixin):
    """Rich object serialization with formatting options."""

    def serialize(
        self,
        flatten=True,
        with_id=True,
        with_class=False,
        case=None,
        capital=True,
        select_fn=None,
        field_prefix=None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Serialize an object with rich formatting options.

        Args:
            flatten: If True, flatten nested serializations into parent dict
            with_id: Include 'id' fields in serialization
            with_class: Add class name to field names
            case: Case transformation ('upper', 'lower', None)
            capital: Capitalize field names
            select_fn: Custom function to select which fields to include
            field_prefix: Prefix to add to field names
        """

        select_fn = select_fn or self._default_select
        result = {}

        for name, value in self.__dict__.items():
            if not select_fn(name, value, with_id=with_id):
                continue

            # Format the key name
            key = self._format_key(
                name,
                with_class=with_class,
                case=case,
                capital=capital,
                field_prefix=field_prefix,
            )

            # Handle nested objects
            if hasattr(value, "serialize"):
                if flatten:
                    # Flatten nested serialization into parent
                    nested = value.serialize(flatten=flatten, **kwargs)
                    if isinstance(nested, dict):
                        # Add prefix to nested keys if specified
                        if field_prefix:
                            nested = {f"{field_prefix}_{k}": v for k, v in nested.items()}
                        result |= nested
                    continue
                else:
                    value = value.serialize(flatten=False, **kwargs)
            elif hasattr(value, "__dict__"):
                # Serialize arbitrary objects
                value = {
                    k: v
                    for k, v in value.__dict__.items()
                    if select_fn(k, v, with_id=with_id)
                }
            elif hasattr(value, "__slots__"):
                # Handle slotted objects
                value = str(value)

            result[key] = value

        return result

    def _default_select(self, key: str, value: Any, with_id: bool = True) -> bool:
        """Default attribute selection logic."""
        return (
            not key.startswith("_")
            and not callable(value)
            and (with_id or key != "id")
            and value is not None
        )

    def _format_key(
        self, key: str, with_class=False, case=None, capital=True, field_prefix=None
    ) -> str:
        """Format key names with various options."""
        # Apply case transformation
        if case == "upper":
            key = key.upper()
        elif case == "lower":
            key = key.lower()
        elif capital:
            key = key.capitalize()

        # Add field prefix
        if field_prefix:
            key = f"{field_prefix}_{key}"

        # Add class prefix
        if with_class:
            class_name = self.__class__.__name__
            if capital:
                class_name = class_name.capitalize()
            elif case == "upper":
                class_name = class_name.upper()
            elif case == "lower":
                class_name = class_name.lower()

            separator = "_" if isinstance(with_class, bool) else str(with_class)
            key = f"{class_name}{separator}{key}"

        return key

    def label(self, name: str, **kwargs) -> str:
        """Legacy method for backward compatibility."""
        return self._format_key(name, **kwargs)


class Namespace(SimpleNamespace, SerializationMixin):
    """Enhanced SimpleNamespace with serialization capabilities."""

    def serialize(self, recursive=True, **kwargs) -> Dict[str, Any]:
        """Serialize namespace to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if recursive and hasattr(value, "serialize"):
                value = value.serialize(recursive=recursive, **kwargs)
            elif recursive and isinstance(value, dict):
                # Convert nested dicts to the proper serialized format
                value = {
                    k: v.serialize(**kwargs) if hasattr(v, "serialize") else v
                    for k, v in value.items()
                }
            elif recursive and isinstance(value, list):
                # Handle lists of serializable objects
                value = [
                    item.serialize(**kwargs) if hasattr(item, "serialize") else item
                    for item in value
                ]
            result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any], recursive=True):
        """Create Namespace from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary")

        if not recursive:
            return cls(**data)
        # Convert nested dicts to Namespaces
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                processed_data[key] = cls.from_dict(value, recursive=True)
            elif isinstance(value, list):
                # Handle lists that might contain dicts
                processed_data[key] = [
                    cls.from_dict(item, recursive=True)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                processed_data[key] = value
        return cls(**processed_data)

    def update(self, **kwargs):
        """Update the namespace with new values."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self

    def get(self, key: str, default=None):
        """Get attribute with default value."""
        return getattr(self, key, default)


class SerializationEncoder(json.JSONEncoder):
    """JSON encoder that handles serialization objects."""

    def default(self, obj):
        if hasattr(obj, "serialize"):
            return obj.serialize()
        elif isinstance(obj, SimpleNamespace):
            return obj.__dict__
        elif is_dataclass(obj):
            return {f.name: getattr(obj, f.name) for f in fields(obj)}
        return super().default(obj)


# Utility functions
def serialize_object(obj: Any, **kwargs) -> Dict[str, Any]:
    """Serialize any object using appropriate method."""
    if hasattr(obj, "serialize"):
        return obj.serialize(**kwargs)
    elif is_dataclass(obj):
        # Convert dataclass to dict
        return {
            f.name: getattr(obj, f.name)
            for f in fields(obj)
            if getattr(obj, f.name) is not None
        }
    elif isinstance(obj, SimpleNamespace):
        return obj.__dict__
    elif hasattr(obj, "__dict__"):
        return {
            k: v
            for k, v in obj.__dict__.items()
            if not k.startswith("_") and not callable(v) and v is not None
        }
    else:
        return {"value": obj}


def to_namespace(data: Dict[str, Any], recursive=True) -> Namespace:
    """Convert dictionary to Namespace."""
    return Namespace.from_dict(data, recursive=recursive)


# Legacy compatibility - standalone serialize function
def _default_select(kk, vv, **kw):
    return (
        not kk.startswith("_")
        and not callable(vv)
        and (kw.get("with_id", True) or kk != "id")
    )


def serialize(obj, flatten=True, with_id=False, select=None):
    """Legacy serialize function for backward compatibility."""
    if select is None:
        select = _default_select

    for k, v in obj.__dict__.items():
        if select(k, v, with_id=with_id):
            if hasattr(v, "__dict__") or hasattr(v, "__slots__"):
                if flatten:
                    yield from serialize(
                        v, flatten=flatten, with_id=with_id, select=select
                    )
                else:
                    yield (
                        k,
                        dict(serialize(v, flatten=False, with_id=with_id, select=select)),
                    )
            else:
                yield k, v
