#!/usr/bin/env python3
import sys
import traceback
import time

import torch
import torch.nn as nn
import torch.nn.functional as F


def _sync(dev):
    if dev.type == "cuda":
        torch.cuda.synchronize()


def _ok(msg=""):
    return {"ok": True, "msg": msg}


def _fail(e: BaseException):
    return {"ok": False, "msg": f"{type(e).__name__}: {e}"}


def run_test(name, fn, dev):
    try:
        _sync(dev)
        t0 = time.perf_counter()
        fn()
        _sync(dev)
        t1 = time.perf_counter()
        return _ok(f"{(t1 - t0)*1000:.2f} ms")
    except Exception as e:
        return _fail(e)


def assert_cuda(t, what="tensor"):
    assert isinstance(t, torch.Tensor), f"{what} is not a torch.Tensor"
    assert t.is_cuda, f"{what} is not CUDA (device={t.device})"


def header():
    print("=== Torch GPU Smoke Test ===")
    print("python:", sys.version.split()[0])
    print("torch:", torch.__version__)
    print("cuda available:", torch.cuda.is_available())
    print("torch.version.cuda:", torch.version.cuda)
    print("cudnn:", torch.backends.cudnn.version())
    print("cudnn enabled:", torch.backends.cudnn.enabled)
    if torch.cuda.is_available():
        print("gpu:", torch.cuda.get_device_name(0))
        print("capability:", torch.cuda.get_device_capability(0))
    print()


def main():
    header()
    if not torch.cuda.is_available():
        print("CUDA not available; nothing to test.")
        sys.exit(1)

    dev = torch.device("cuda:0")

    # Conservative cuDNN settings for old GPUs
    torch.backends.cudnn.enabled = True
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    results = []

    # --------------------
    # Core pointwise math
    # --------------------
    def t_pointwise():
        x = torch.randn(1024, device=dev, dtype=torch.float32, requires_grad=True)
        y = torch.randn(1024, device=dev, dtype=torch.float32, requires_grad=True)
        z = (x + y) * 0.5
        z = z - x / (y.abs() + 1.0)
        z = torch.pow(z, 2.0)
        z = torch.sqrt(z + 1e-3)
        z = torch.exp(torch.log(z + 1.0))
        z = torch.abs(z)
        z = torch.clamp(z, -1.0, 1.0)
        assert_cuda(z, "z")
        z.sum().backward()

    results.append(("pointwise add/sub/mul/div/pow/sqrt/exp/log/abs/clamp", run_test("pointwise", t_pointwise, dev)))

    # --------------------
    # where / broadcasting
    # --------------------
    def t_where_bcast():
        a = torch.randn(128, 1, 64, device=dev)
        b = torch.randn(1, 32, 64, device=dev)
        cond = (a > 0)
        out = torch.where(cond, a, b)  # broadcast
        assert_cuda(out, "out")

    results.append(("where + broadcasting", run_test("where+bcast", t_where_bcast, dev)))

    # --------------------
    # reductions / arg*
    # --------------------
    def t_reductions():
        x = torch.randn(256, 128, device=dev)
        s = x.sum()
        m = x.mean()
        mx = x.max()
        mn = x.min()
        am = x.argmax(dim=1)
        an = x.argmin(dim=1)
        for t, n in [(s, "sum"), (m, "mean"), (mx, "max"), (mn, "min")]:
            assert_cuda(t, n)
        assert_cuda(am, "argmax")
        assert_cuda(an, "argmin")

    results.append(("reductions sum/mean/min/max/argmin/argmax", run_test("reductions", t_reductions, dev)))

    # --------------------
    # reshape/view/permute/transpose
    # --------------------
    def t_reshape():
        x = torch.randn(8, 3, 32, 32, device=dev)
        y = x.view(8, 3, 1024)
        z = y.transpose(1, 2).permute(0, 2, 1)
        w = z.reshape(8, 1024, 3)
        assert_cuda(w, "w")

    results.append(("reshape/view/transpose/permute", run_test("reshape", t_reshape, dev)))

    # --------------------
    # cat/stack/split
    # --------------------
    def t_cat_stack_split():
        xs = [torch.randn(64, 16, device=dev) for _ in range(4)]
        c = torch.cat(xs, dim=0)
        s = torch.stack(xs, dim=0)
        sp = torch.split(c, 64, dim=0)
        assert_cuda(c, "cat")
        assert_cuda(s, "stack")
        assert len(sp) == 4 and all(t.is_cuda for t in sp), "split did not produce CUDA tensors"

    results.append(("cat/stack/split", run_test("cat/stack/split", t_cat_stack_split, dev)))

    # --------------------
    # advanced indexing (can be a trouble spot on old GPUs)
    # --------------------
    def t_indexing():
        x = torch.randn(128, 64, device=dev)
        idx = torch.randint(0, 128, (32,), device=dev)
        y = x[idx]          # fancy index
        z = x[:, 10:20]     # slice
        assert_cuda(y, "y")
        assert_cuda(z, "z")

    results.append(("indexing fancy+slice", run_test("indexing", t_indexing, dev)))

    # --------------------
    # Linear algebra via cuBLAS: mm / bmm / addmm / matmul / einsum
    # --------------------
    def t_mm():
        a = torch.randn(2048, 2048, device=dev)
        b = torch.randn(2048, 2048, device=dev)
        c = a @ b
        assert_cuda(c, "matmul")
        d = torch.mm(a, b)
        assert_cuda(d, "mm")

    results.append(("matmul/@ and mm", run_test("mm", t_mm, dev)))

    def t_bmm_addmm():
        a = torch.randn(32, 256, 128, device=dev)
        b = torch.randn(32, 128, 64, device=dev)
        c = torch.bmm(a, b)
        assert_cuda(c, "bmm")
        m = torch.randn(256, 128, device=dev)
        n = torch.randn(128, 64, device=dev)
        inp = torch.randn(256, 64, device=dev)
        out = torch.addmm(inp, m, n)
        assert_cuda(out, "addmm")

    results.append(("bmm + addmm", run_test("bmm+addmm", t_bmm_addmm, dev)))

    def t_einsum():
        a = torch.randn(128, 64, device=dev)
        b = torch.randn(64, 32, device=dev)
        c = torch.einsum("ij,jk->ik", a, b)
        assert_cuda(c, "einsum")

    results.append(("einsum basic", run_test("einsum", t_einsum, dev)))

    # --------------------
    # Convolution / pooling (cuDNN typically)
    # --------------------
    def t_conv2d():
        x = torch.randn(8, 3, 128, 128, device=dev, requires_grad=True)
        conv = nn.Conv2d(3, 16, 3, padding=1).to(dev)
        y = conv(x)
        assert_cuda(y, "conv2d output")
        y.mean().backward()

    results.append(("nn.Conv2d forward+backward", run_test("conv2d", t_conv2d, dev)))

    def t_convtranspose2d():
        x = torch.randn(4, 8, 64, 64, device=dev)
        deconv = nn.ConvTranspose2d(8, 4, 4, stride=2, padding=1).to(dev)
        y = deconv(x)
        assert_cuda(y, "convT output")

    results.append(("nn.ConvTranspose2d", run_test("convT2d", t_convtranspose2d, dev)))

    def t_pooling():
        x = torch.randn(8, 16, 64, 64, device=dev)
        y = F.max_pool2d(x, 2)
        z = F.avg_pool2d(x, 2)
        a = F.adaptive_avg_pool2d(x, (1, 1))
        assert_cuda(y, "maxpool")
        assert_cuda(z, "avgpool")
        assert_cuda(a, "adaptive avgpool")

    results.append(("pooling max/avg/adaptive_avg", run_test("pooling", t_pooling, dev)))

    # --------------------
    # Normalization
    # --------------------
    def t_norms():
        x = torch.randn(16, 32, 32, 32, device=dev, requires_grad=True)
        bn = nn.BatchNorm2d(32).to(dev)
        y = bn(x)
        gn = nn.GroupNorm(8, 32).to(dev)
        z = gn(x)
        ln = nn.LayerNorm([32, 32, 32]).to(dev)
        w = ln(x)
        for t, n in [(y, "bn"), (z, "gn"), (w, "ln")]:
            assert_cuda(t, n)
        (y.mean() + z.mean() + w.mean()).backward()

    results.append(("BatchNorm2d / GroupNorm / LayerNorm (fw+bw)", run_test("norms", t_norms, dev)))

    # --------------------
    # Activations
    # --------------------
    def t_activations():
        x = torch.randn(1024, device=dev, requires_grad=True)
        y = F.relu(x)
        z = F.leaky_relu(x, 0.1)
        e = F.elu(x)
        s = torch.sigmoid(x)
        t = torch.tanh(x)
        g = F.gelu(x)
        sm = F.softmax(x.view(32, 32), dim=1)
        for u, n in [(y,"relu"), (z,"lrelu"), (e,"elu"), (s,"sigmoid"), (t,"tanh"), (g,"gelu"), (sm,"softmax")]:
            assert_cuda(u, n)
        (y.sum() + z.sum() + e.sum() + s.sum() + t.sum() + g.sum() + sm.sum()).backward()

    results.append(("activations relu/leaky_relu/elu/sigmoid/tanh/gelu/softmax", run_test("activations", t_activations, dev)))

    # --------------------
    # Losses
    # --------------------
    def t_losses():
        # CrossEntropyLoss
        logits = torch.randn(64, 10, device=dev, requires_grad=True)
        target = torch.randint(0, 10, (64,), device=dev)
        ce = F.cross_entropy(logits, target)
        assert_cuda(ce, "cross_entropy loss")
        ce.backward()

        # MSELoss
        a = torch.randn(256, device=dev, requires_grad=True)
        b = torch.randn(256, device=dev)
        mse = F.mse_loss(a, b)
        assert_cuda(mse, "mse loss")
        mse.backward()

        # BCEWithLogitsLoss
        p = torch.randn(128, device=dev, requires_grad=True)
        q = torch.randint(0, 2, (128,), device=dev).float()
        bce = F.binary_cross_entropy_with_logits(p, q)
        assert_cuda(bce, "bce loss")
        bce.backward()

        # NLLLoss (log-softmax + nll)
        logits2 = torch.randn(32, 7, device=dev, requires_grad=True)
        tgt2 = torch.randint(0, 7, (32,), device=dev)
        logp = F.log_softmax(logits2, dim=1)
        nll = F.nll_loss(logp, tgt2)
        assert_cuda(nll, "nll loss")
        nll.backward()

    results.append(("losses cross_entropy/mse/bce_with_logits/nll", run_test("losses", t_losses, dev)))

    # --------------------
    # Optimizers (basic step smoke-test)
    # --------------------
    def t_optimizers():
        torch.manual_seed(0)
        model = nn.Sequential(
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Linear(256, 10),
        ).to(dev)

        x = torch.randn(64, 128, device=dev)
        y = torch.randint(0, 10, (64,), device=dev)

        # SGD
        opt = torch.optim.SGD(model.parameters(), lr=1e-2, momentum=0.9)
        opt.zero_grad(set_to_none=True)
        loss = F.cross_entropy(model(x), y)
        loss.backward()
        opt.step()

        # Adam
        opt2 = torch.optim.Adam(model.parameters(), lr=1e-3)
        opt2.zero_grad(set_to_none=True)
        loss2 = F.cross_entropy(model(x), y)
        loss2.backward()
        opt2.step()

    results.append(("optimizers SGD+Adam step", run_test("optimizers", t_optimizers, dev)))

    # --------------------
    # Print results
    # --------------------
    passed = 0
    failed = 0
    print("=== Results (PASS/FAIL) ===")
    for name, r in results:
        if r["ok"]:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"
        print(f"{status:4} | {name} | {r['msg']}")

    print()
    print(f"Summary: {passed} passed, {failed} failed, {passed+failed} total")

    # Exit code: 0 if all pass; 2 otherwise
    sys.exit(0 if failed == 0 else 2)


if __name__ == "__main__":
    main()

