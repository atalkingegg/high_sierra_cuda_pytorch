#!/usr/bin/env python3

import sys, time
import numpy as np
import torch

print("Python:", sys.version.split()[0])
print("NumPy:", np.__version__)
print("Torch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
print("CUDA version:", torch.version.cuda)
print("cuDNN:", torch.backends.cudnn.version(), "enabled:", torch.backends.cudnn.enabled)

def bench(fn, iters=200, warmup=50):
    for _ in range(warmup): fn()
    t0 = time.time()
    for _ in range(iters): fn()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    return (time.time() - t0) / iters

device = "cuda" if torch.cuda.is_available() else "cpu"
x = torch.randn(4096, 4096, device=device)

t = bench(lambda: (x @ x).sum().item(), iters=50, warmup=5)
print("matmul+sum avg sec:", t)

