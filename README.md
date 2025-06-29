# Simple Serialization

A unified serialization library for Python objects that combines dataclass serialization, rich object serialization, and namespace handling into a single, comprehensive package.

## Features

- **Unified API**: All serialization classes inherit from a common `SerializationMixin`
- **Dataclass Support**: Enhanced dataclass serialization with field mapping and exclusions
- **Rich Object Serialization**: Advanced formatting options including flattening, case transformations, and class prefixing
- **Namespace Handling**: Enhanced SimpleNamespace with full serialization capabilities
- **JSON Support**: Built-in JSON encoding for all serialization objects
- **Backward Compatibility**: Legacy `serialize()` function preserved
- **No Dependencies**: Pure Python with no external dependencies

## Installation

```bash
pip install simple-serialization
```

## Quick Start

```python
from serialization import DataclassSerializer, ObjectSerializer, Namespace

# Dataclass serialization
from dataclasses import dataclass

@dataclass
class User(DataclassSerializer):
    name: str
    email: str
    age: int

    _field_map = {"email": "email_address"}
    _exclude_fields = {"age"}

user = User(name="John", email="john@example.com", age=30)
result = user.serialize()
# {"name": "John", "email_address": "john@example.com"}

# Object serialization
class Product(ObjectSerializer):
    def __init__(self):
        self.name = "laptop"
        self.price = 999.99
        self.category = "electronics"

product = Product()
result = product.serialize(with_class=True, case="upper")
# {"PRODUCT_NAME": "laptop", "PRODUCT_PRICE": 999.99, "PRODUCT_CATEGORY": "electronics"}

# Namespace handling
config = Namespace.from_dict({
    "database": {"host": "localhost", "port": 5432},
    "cache": {"enabled": True, "ttl": 300}
})
print(config.database.host)  # "localhost"
result = config.serialize()
# {"database": {"host": "localhost", "port": 5432}, "cache": {"enabled": True, "ttl": 300}}
```

## API Reference

### SerializationMixin (Base Class)

Base mixin providing common serialization functionality.

**Methods:**

- `serialize(**kwargs) -> Dict[str, Any]`: Abstract method to serialize the object
- `to_dict(**kwargs) -> Dict[str, Any]`: Alias for serialize() returning a dict
- `to_json(indent=None, **kwargs) -> str`: Serialize to JSON string

### DataclassSerializer

Enhanced dataclass serialization with field mapping and exclusions.

**Class Configuration:**

- `_field_map: Dict[str, str]`: Maps field names to serialized names
- `_exclude_fields: set`: Fields to exclude from serialization
- `_default_values: Dict[str, Any]`: Default values for missing fields

**Methods:**

- `serialize(nested=True, **kwargs) -> Dict[str, Any]`: Serialize dataclass with field mapping

**Example:**

```python
from dataclasses import dataclass
from serialization import DataclassSerializer

@dataclass
class Person(DataclassSerializer):
    first_name: str
    last_name: str
    email: str
    age: int

    # Configuration
    _field_map = {"first_name": "firstName", "last_name": "lastName"}
    _exclude_fields = {"age"}

    def value_of_email(self, value):
        """Custom value transformer"""
        return value.lower()

person = Person("John", "Doe", "JOHN@EXAMPLE.COM", 30)
result = person.serialize()
# {"firstName": "John", "lastName": "Doe", "email": "john@example.com"}
```

### ObjectSerializer

Rich object serialization with advanced formatting options.

**Methods:**

- `serialize(flatten=True, with_id=True, with_class=False, case=None, capital=True, select_fn=None, field_prefix=None, **kwargs) -> Dict[str, Any]`

**Parameters:**

- `flatten`: If True, flatten nested serializations into parent dict
- `with_id`: Include 'id' fields in serialization
- `with_class`: Add class name to field names
- `case`: Case transformation ('upper', 'lower', None)
- `capital`: Capitalize field names
- `select_fn`: Custom function to select which fields to include
- `field_prefix`: Prefix to add to field names

**Example:**

```python
from serialization import ObjectSerializer

class Order(ObjectSerializer):
    def __init__(self):
        self.id = 12345
        self.customer_name = "John Doe"
        self.total_amount = 299.99
        self.status = "pending"

class OrderItem(ObjectSerializer):
    def __init__(self):
        self.name = "Widget"
        self.quantity = 2
        self.price = 149.99

class ComplexOrder(ObjectSerializer):
    def __init__(self):
        self.order_id = 67890
        self.item = OrderItem()

# Basic serialization
order = Order()
result = order.serialize()
# {"Id": 12345, "Customer_name": "John Doe", "Total_amount": 299.99, "Status": "pending"}

# Without ID fields
result = order.serialize(with_id=False)
# {"Customer_name": "John Doe", "Total_amount": 299.99, "Status": "pending"}

# With class prefix
result = order.serialize(with_class=True)
# {"Order_Id": 12345, "Order_Customer_name": "John Doe", ...}

# Case transformations
result = order.serialize(case="upper", capital=False)
# {"ID": 12345, "CUSTOMER_NAME": "John Doe", ...}

# Flattening nested objects
complex_order = ComplexOrder()
result = complex_order.serialize(flatten=True)
# {"Order_id": 67890, "Name": "Widget", "Quantity": 2, "Price": 149.99}

# No flattening
result = complex_order.serialize(flatten=False)
# {"Order_id": 67890, "Item": {"Name": "Widget", "Quantity": 2, "Price": 149.99}}

# Custom field selection
def select_important_fields(key, value, **kwargs):
    return key in ['customer_name', 'total_amount']

result = order.serialize(select_fn=select_important_fields)
# {"Customer_name": "John Doe", "Total_amount": 299.99}
```

### Namespace

Enhanced SimpleNamespace with serialization capabilities.

**Methods:**

- `serialize(recursive=True, **kwargs) -> Dict[str, Any]`: Serialize namespace to dictionary
- `from_dict(data: Dict[str, Any], recursive=True) -> Namespace`: Create Namespace from dictionary (class method)
- `update(**kwargs) -> Namespace`: Update namespace with new values
- `get(key: str, default=None) -> Any`: Get attribute with default value

**Example:**

```python
from serialization import Namespace

# Create from a dictionary
config_data = {
    "app": {
        "name": "MyApp",
        "version": "1.0.0",
        "features": ["auth", "api", "cache"]
    },
    "database": {
        "host": "localhost",
        "port": 5432,
        "ssl": True
    }
}

config = Namespace.from_dict(config_data)

# Access with dot notation
print(config.app.name)  # "MyApp"
print(config.database.port)  # 5432
print(config.app.features)  # ["auth", "api", "cache"]

# Update values
config.update(environment="production")
config.app.update(debug=False)

# Serialize back to dict
result = config.serialize()
# Returns the full nested dictionary structure

# Get with defaults
timeout = config.get("timeout", 30)  # 30 (default)
db_host = config.database.get("host", "127.0.0.1")  # "localhost"

# JSON serialization
json_str = config.to_json(indent=2)
```

### SerializationEncoder

JSON encoder that handles all serialization objects.

**Example:**

```python
import json
from serialization import SerializationEncoder, Namespace

# Works with any serializable object
data = {
    "config": Namespace(host="localhost", port=8080),
    "items": [Namespace(id=1, name="item1"), Namespace(id=2, name="item2")]
}

json_str = json.dumps(data, cls=SerializationEncoder, indent=2)
# {
#   "config": {
#     "host": "localhost",
#     "port": 8080
#   },
#   "items": [
#     {
#       "id": 1,
#       "name": "item1"
#     },
#     {
#       "id": 2,
#       "name": "item2"
#     }
#   ]
# }
```

### Utility Functions

#### serialize_object(obj, **kwargs)

Serialize any object using the appropriate method.

```python
from serialization import serialize_object
from dataclasses import dataclass

@dataclass
class Item:
    name: str
    price: float

item = Item("laptop", 999.99)
result = serialize_object(item)
# {"name": "laptop", "price": 999.99}
```

#### to_namespace(data, recursive=True)

Convert dictionary to Namespace.

```python
from serialization import to_namespace

data = {"user": {"name": "John", "age": 30}}
ns = to_namespace(data)
print(ns.user.name)  # "John"
```

#### serialize(obj, flatten=True, with_id=False, select=None)

Legacy serialize function for backward compatibility.

```python
from serialization import serialize

class Item:
    def __init__(self):
        self.name = "test"
        self.value = 42

item = Item()
result = dict(serialize(item))
# {"name": "test", "value": 42}
```

## Advanced Usage

### Custom Value Transformers

DataclassSerializer supports custom value transformers:

```python
from dataclasses import dataclass
from datetime import datetime
from serialization import DataclassSerializer

@dataclass
class Event(DataclassSerializer):
    name: str
    timestamp: datetime
    priority: int

    def value_of_timestamp(self, value):
        """Convert datetime to ISO string"""
        return value.isoformat() if value else None

    def value_of_priority(self, value):
        """Convert priority number to text"""
        priorities = {1: "low", 2: "medium", 3: "high"}
        return priorities.get(value, "unknown")

event = Event("Meeting", datetime.now(), 2)
result = event.serialize()
# {"name": "Meeting", "timestamp": "2023-12-07T14:30:00", "priority": "medium"}
```

### Nested Object Serialization

Handle complex nested structures:

```python
from dataclasses import dataclass
from serialization import DataclassSerializer

@dataclass
class Address(DataclassSerializer):
    street: str
    city: str
    zip_code: str

@dataclass
class Person(DataclassSerializer):
    name: str
    email: str
    address: Address

person = Person(
    name="John Doe",
    email="john@example.com",
    address=Address("123 Main St", "Anytown", "12345")
)

result = person.serialize()
# {
#   "name": "John Doe",
#   "email": "john@example.com",
#   "address": {
#     "street": "123 Main St",
#     "city": "Anytown",
#     "zip_code": "12345"
#   }
# }
```

### Complex Object Hierarchies

ObjectSerializer can handle complex object hierarchies with flattening:

```python
from serialization import ObjectSerializer

class Address(ObjectSerializer):
    def __init__(self):
        self.street = "123 Main St"
        self.city = "Anytown"

class Person(ObjectSerializer):
    def __init__(self):
        self.name = "John Doe"
        self.email = "john@example.com"
        self.address = Address()

person = Person()

# Flattened output
result = person.serialize(flatten=True)
# {"Name": "John Doe", "Email": "john@example.com", "Street": "123 Main St", "City": "Anytown"}

# Nested output
result = person.serialize(flatten=False)
# {"Name": "John Doe", "Email": "john@example.com", "Address": {"Street": "123 Main St", "City": "Anytown"}}
```

## Testing

Run the test suite:

```bash
pytest
```

With coverage:

```bash
pytest --cov=simple_serialization --cov-report=html
```

## License

MIT License. See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request
