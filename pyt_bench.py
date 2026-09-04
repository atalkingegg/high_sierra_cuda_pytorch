#!/usr/bin/env python3
import os, time, platform
import torch

def sync(dev):
    if dev.type == "cuda":
        torch.cuda.synchronize()

def bench(fn, dev, warmup=10, iters=50):
    # Warmup
    for _ in range(warmup):
        fn()
    sync(dev)

    t0 = time.perf_counter()
    for _ in range(iters):
        fn()
    sync(dev)
    t1 = time.perf_counter()

    return (t1 - t0) * 1000.0 / iters  # ms/iter

def gflops_matmul(n, ms):
    # GEMM: (n x n) @ (n x n) ~ 2*n^3 FLOPs
    flops = 2.0 * (n**3)
    return flops / (ms/1000.0) / 1e9

def main():
    print("=== System ===")
    print("Platform:", platform.platform())
    print("Python:", platform.python_version())
    print("Torch:", torch.__version__)
    print("CUDA available:", torch.cuda.is_available())
    print("Torch CUDA:", torch.version.cuda)
    print("cuDNN:", torch.backends.cudnn.version())
    print("cuDNN enabled:", torch.backends.cudnn.enabled)
    if torch.cuda.is_available():
        print("GPU:", torch.cuda.get_device_name(0))
        print("GPU capability:", torch.cuda.get_device_capability(0))
    print()

    torch.set_num_threads(os.cpu_count() or 1)

    # -------- CPU matmul --------
    n_cpu = 2048
    a = torch.randn(n_cpu, n_cpu, device="cpu", dtype=torch.float32)
    b = torch.randn(n_cpu, n_cpu, device="cpu", dtype=torch.float32)

    def cpu_mm():
        _ = a @ b

    ms = bench(cpu_mm, torch.device("cpu"), warmup=3, iters=100)
    print(f"[CPU] matmul {n_cpu}x{n_cpu}: {ms:.2f} ms/iter  (~{gflops_matmul(n_cpu, ms):.1f} GFLOP/s)")
    print()

    if not torch.cuda.is_available():
        return

    # Suggest consistent flags
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    # -------- CUDA matmul --------
    # Use sizes that fit both GPUs; 4096 may be too heavy on 750M depending on memory fragmentation
    n_gpu = 2048
    dev = torch.device("cuda:0")
    ag = torch.randn(n_gpu, n_gpu, device=dev, dtype=torch.float32)
    bg = torch.randn(n_gpu, n_gpu, device=dev, dtype=torch.float32)

    def gpu_mm():
        _ = ag @ bg

    ms = bench(gpu_mm, dev, warmup=10, iters=250)
    print(f"[CUDA] matmul {n_gpu}x{n_gpu}: {ms:.2f} ms/iter  (~{gflops_matmul(n_gpu, ms):.1f} GFLOP/s)")
    print()

if __name__ == "__main__":
    main()

