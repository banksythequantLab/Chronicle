"""The convergence money shot: memory-off oscillates, memory-on converges."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from memory_core import run

off, on = run(False), run(True)
plt.rcParams.update({"figure.facecolor": "#0d1117", "axes.facecolor": "#161b22",
                     "text.color": "#e9edf2", "axes.labelcolor": "#e9edf2",
                     "xtick.color": "#8b949e", "ytick.color": "#8b949e",
                     "axes.edgecolor": "#30363d"})
plt.figure(figsize=(8, 4.5))
x = range(len(on))
plt.plot(x, off, "-o", color="#ef4444", lw=2, label="memory OFF (oscillates)")
plt.plot(x, on, "-o", color="#3fb950", lw=2, label="CockroachDB memory ON (converges)")
plt.axhline(1.0, ls="--", color="#f0b429", alpha=.5)
plt.text(0.2, 1.02, "truth (claim is TRUE)", color="#f0b429", fontsize=9)
plt.ylim(0, 1.12)
plt.xlabel("discovery batch (rolling review)")
plt.ylabel("theory confidence")
plt.title("Living theory of the case: persistent memory drives convergence",
          color="#f0b429", fontweight="bold")
plt.legend(loc="lower right")
plt.tight_layout()
out = os.path.join(os.path.dirname(__file__), "..", "docs", "convergence.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
plt.savefig(out, dpi=130)
print("wrote", out)
