import re
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict

_TAG = re.compile(r"<[^>]*>")


def clean_text(v):
    """Strip HTML tags and control chars from user text (React escapes on output; this is defence in depth)."""
    if isinstance(v, str):
        v = _TAG.sub("", v)
        v = "".join(ch for ch in v if ch == "\n" or ch == "\t" or ord(ch) >= 32)
        return v.strip()
    return v


CleanStr = Annotated[str, BeforeValidator(clean_text)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
