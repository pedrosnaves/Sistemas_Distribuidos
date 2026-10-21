from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Operation(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ADD: _ClassVar[Operation]
    SUBTRACT: _ClassVar[Operation]
    MULTIPLY: _ClassVar[Operation]
    DIVIDE: _ClassVar[Operation]
ADD: Operation
SUBTRACT: Operation
MULTIPLY: Operation
DIVIDE: Operation

class Name(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class Address(_message.Message):
    __slots__ = ("host", "port")
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    host: str
    port: int
    def __init__(self, host: _Optional[str] = ..., port: _Optional[int] = ...) -> None: ...

class Binding(_message.Message):
    __slots__ = ("name", "address")
    NAME_FIELD_NUMBER: _ClassVar[int]
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    name: str
    address: Address
    def __init__(self, name: _Optional[str] = ..., address: _Optional[_Union[Address, _Mapping]] = ...) -> None: ...

class Status(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class Calculation(_message.Message):
    __slots__ = ("a", "b", "operation")
    A_FIELD_NUMBER: _ClassVar[int]
    B_FIELD_NUMBER: _ClassVar[int]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    a: float
    b: float
    operation: Operation
    def __init__(self, a: _Optional[float] = ..., b: _Optional[float] = ..., operation: _Optional[_Union[Operation, str]] = ...) -> None: ...

class CalculationResult(_message.Message):
    __slots__ = ("result", "machine", "process_id")
    RESULT_FIELD_NUMBER: _ClassVar[int]
    MACHINE_FIELD_NUMBER: _ClassVar[int]
    PROCESS_ID_FIELD_NUMBER: _ClassVar[int]
    result: float
    machine: str
    process_id: int
    def __init__(self, result: _Optional[float] = ..., machine: _Optional[str] = ..., process_id: _Optional[int] = ...) -> None: ...

class TextRequest(_message.Message):
    __slots__ = ("text",)
    TEXT_FIELD_NUMBER: _ClassVar[int]
    text: str
    def __init__(self, text: _Optional[str] = ...) -> None: ...

class TextAnalysis(_message.Message):
    __slots__ = ("uppercase", "characters", "words", "machine", "process_id")
    UPPERCASE_FIELD_NUMBER: _ClassVar[int]
    CHARACTERS_FIELD_NUMBER: _ClassVar[int]
    WORDS_FIELD_NUMBER: _ClassVar[int]
    MACHINE_FIELD_NUMBER: _ClassVar[int]
    PROCESS_ID_FIELD_NUMBER: _ClassVar[int]
    uppercase: str
    characters: int
    words: int
    machine: str
    process_id: int
    def __init__(self, uppercase: _Optional[str] = ..., characters: _Optional[int] = ..., words: _Optional[int] = ..., machine: _Optional[str] = ..., process_id: _Optional[int] = ...) -> None: ...
