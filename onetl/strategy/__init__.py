# SPDX-FileCopyrightText: 2021-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from onetl.strategy.base_strategy import BaseStrategy
from onetl.strategy.incremental_strategy import (
    IncrementalBatchStrategy,
    IncrementalStrategy,
)
from onetl.strategy.snapshot_strategy import SnapshotBatchStrategy, SnapshotStrategy
from onetl.strategy.strategy_manager import StrategyManager
