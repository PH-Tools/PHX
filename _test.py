from pydantic import BaseModel, ValidationError, validator
from typing import List, Union, Optional


class BaseType(BaseModel):
    type_: int


class TypeA(BaseType):
    data_a: str


class TypeB(BaseType):
    data_b: str


class TypeC(BaseType):
    data_c: str


class MyModel(BaseModel):
    types: List[BaseType]

    @validator("types")
    def validate_types(cls, value, values):
        print("value=", value)
        print("values=", values)


d = {
    "types": [
        {"type_": 1, "data_a": "a"},
        {"type_": 2, "data_b": "b"},
        {"type_": 3, "data_c": "c"},
    ]
}

m = MyModel.parse_obj(d)

print(m)
