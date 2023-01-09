# Copyright The PyTorch Lightning team.
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
from pytorch_lightning.accelerators.accelerator import Accelerator
from pytorch_lightning.accelerators.cpu import CPUAccelerator
from pytorch_lightning.accelerators.gpu import GPUAccelerator
from pytorch_lightning.accelerators.hpu import HPUAccelerator
from pytorch_lightning.accelerators.ipu import IPUAccelerator
from pytorch_lightning.accelerators.registry import AcceleratorRegistry, call_register_accelerators
from pytorch_lightning.accelerators.tpu import TPUAccelerator

ACCELERATORS_BASE_MODULE = "pytorch_lightning.accelerators"

call_register_accelerators(ACCELERATORS_BASE_MODULE)
