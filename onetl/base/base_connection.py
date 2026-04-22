# SPDX-FileCopyrightText: 2022-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from abc import ABC, abstractmethod
from typing import TypeVar

T = TypeVar("T")


class BaseConnection(ABC):
    """
    Generic connection class
    """

    @abstractmethod
    def check(self: T) -> T:
        """Check source availability. [![support hooks](https://img.shields.io/badge/%20-support%20hooks-blue)](/hooks/)

        If not, an exception will be raised.

        Returns
        -------
        Connection itself

        Raises
        ------
        RuntimeError
            If the connection is not available

        Examples
        --------

        ```python
        connection.check()
        ```
        """
