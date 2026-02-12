import time
import statistics as stats
import argparse

import torch
import torchvision.models as models


def bench_forward(model, x, n_warmup=50, n_runs=1000):
    model.eval()

    # Warmup
    with torch.no_grad():
        for _ in range(n_warmup):
            _ = model(x)

    # Timed runs
    times_ms = []
    with torch.no_grad():
        for _ in range(n_runs):
            t0 = time.perf_counter()
            _ = model(x)
            t1 = time.perf_counter()
            times_ms.append((t1 - t0) * 1000.0)

    return {
        "mean_ms": stats.mean(times_ms),
        "median_ms": stats.median(times_ms),
        "stdev_ms": stats.pstdev(times_ms),
        "min_ms": min(times_ms),
        "max_ms": max(times_ms),
        "n": n_runs,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="resnet18", choices=["resnet18", "resnet50", "mobilenet_v3_small"])
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--warmup", type=int, default=50)
    parser.add_argument("--runs", type=int, default=1000)
    parser.add_argument("--threads", type=int, default=0, help="0 = leave default")
    args = parser.parse_args()

    if args.threads > 0:
        torch.set_num_threads(args.threads)

    device = torch.device("cpu")

    # Pick a model (random weights is fine for pure timing)
    if args.model == "resnet18":
        model = models.resnet18(weights=None)
        x = torch.randn(args.batch, 3, 224, 224)
    elif args.model == "resnet50":
        model = models.resnet50(weights=None)
        x = torch.randn(args.batch, 3, 224, 224)
    else:
        model = models.mobilenet_v3_small(weights=None)
        x = torch.randn(args.batch, 3, 224, 224)

    model = model.to(device)
    x = x.to(device)

    result = bench_forward(model, x, n_warmup=args.warmup, n_runs=args.runs)

    print("=== NN Model Forward-Pass Benchmark (CPU) ===")
    print(f"Model: {args.model}, batch={args.batch}, warmup={args.warmup}, runs={args.runs}, threads={args.threads or 'default'}")
    print(result)


if __name__ == "__main__":
    main()
