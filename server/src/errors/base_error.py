from typing import ClassVar


class BbsError(Exception):
    code: ClassVar[str]
    description: ClassVar[str]
