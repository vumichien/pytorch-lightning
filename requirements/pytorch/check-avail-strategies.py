import bagua
import deepspeed
import fairscale
import horovod.torch

# returns an error code
assert horovod.torch.nccl_built()
