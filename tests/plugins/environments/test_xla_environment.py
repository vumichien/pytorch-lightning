# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
from unittest import mock

import pytest
from tests.helpers.runif import RunIf

import pytorch_lightning as pl
from pytorch_lightning.plugins.environments import XLAEnvironment


@RunIf(tpu=True)
@mock.patch.dict(os.environ, {}, clear=True)
def test_default_attributes():
    """Test the default attributes when no environment variables are set."""
    env = XLAEnvironment()
    assert not env.creates_processes_externally
    assert env.world_size() == 1
    assert env.global_rank() == 0
    assert env.local_rank() == 0
    assert env.node_rank() == 0

    with pytest.raises(KeyError):
        # main_address is required to be passed as env variable
        _ = env.main_address
    with pytest.raises(KeyError):
        # main_port is required to be passed as env variable
        _ = env.main_port


@RunIf(tpu=True)
@mock.patch.dict(
    os.environ,
    {
        "TPU_MESH_CONTROLLER_ADDRESS": "1.2.3.4",
        "TPU_MESH_CONTROLLER_PORT": "500",
        "XRT_SHARD_WORLD_SIZE": "1",
        "XRT_SHARD_ORDINAL": "0",
        "XRT_SHARD_LOCAL_ORDINAL": "2",
        "XRT_HOST_ORDINAL": "3",
    },
    clear=True,
)
def test_attributes_from_environment_variables():
    """Test that the default cluster environment takes the attributes from the environment variables."""
    env = XLAEnvironment()
    assert env.main_address == "1.2.3.4"
    assert env.main_port == 500
    assert env.world_size() == 1
    assert env.global_rank() == 0
    assert env.local_rank() == 2
    assert env.node_rank() == 3
    env.set_global_rank(100)
    assert env.global_rank() == 0
    env.set_world_size(100)
    assert env.world_size() == 1


def test_detect(monkeypatch):
    """Test the detection of a xla environment configuration."""
    monkeypatch.setattr(pl.plugins.environments.xla_environment, "_TPU_AVAILABLE", False)
    assert not XLAEnvironment.detect()

    monkeypatch.setattr(pl.plugins.environments.xla_environment, "_TPU_AVAILABLE", True)
    assert XLAEnvironment.detect()
