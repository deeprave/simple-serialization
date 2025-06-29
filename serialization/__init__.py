# -*- coding: utf-8 -*-
"""
Simple Serialization - A unified serialization library for Python objects.

This package provides a comprehensive serialization framework that unifies
dataclass serialization, rich object serialization, and namespace handling.
"""

from .serialization import (
    SerializationMixin,
    DataclassSerializer,
    ObjectSerializer,
    Namespace,
    SerializationEncoder,
    serialize_object,
    to_namespace,
    serialize,
)

__version__ = "1.0.0"
__author__ = "Simple Serialization Contributors"
__email__ = "simple-serialization@example.com"

__all__ = [
    "SerializationMixin",
    "DataclassSerializer",
    "ObjectSerializer",
    "Namespace",
    "SerializationEncoder",
    "serialize_object",
    "to_namespace",
    "serialize",
]
