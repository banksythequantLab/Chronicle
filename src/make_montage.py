"""Nota.Lawyer suite montage: five memory-ablation charts in one panel.

Chronicle's convergence curve is the hero (top); the four task agents sit
below. One image that says: five agents, one CockroachDB memory, five proofs
that persistent memory changes the OUTCOME.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.gridspec import GridSpec

hero = (r"B:\Chronicle\docs\convergence.png",
        "Chronicle — living theory converges to truth (0.98), memory-off lands wrong (0.42)")
row = [
 (r"B:\ColdCase\docs\ablation.png",         "Cold Case — POIs found: memory vs none"),
 (r"B:\Witness\docs\impeachment_growth.png","Witness — 12/12 contradictions vs 3/12"),
 (r"B:\GapHunter\docs\gap_convergence.png", "Gap Hunter — 6/6 gaps @100% vs 37%"),
 (r"B:\HoldFirewall\docs\spoliation.png",   "Hold Firewall — 0 evidence lost vs 119"),
]

fig = plt.figure(figsize=(16, 12), facecolor="#0d1117")
gs = GridSpec(2, 4, figure=fig, height_ratios=[1.3, 1.0], hspace=0.05, wspace=0.06)

def panel(ax, path):
    ax.imshow(mpimg.imread(path)); ax.axis("off")

ax_hero = fig.add_subplot(gs[0, :])
panel(ax_hero, hero[0])
ax_hero.set_title("Chronicle (hero) — theory converges to truth 0.98  ·  memory-off lands wrong 0.42",
                  color="#f0f6fc", fontsize=16, pad=10)
for i,(p,c) in enumerate(row):
    panel(fig.add_subplot(gs[1, i]), p)

fig.suptitle("Nota.Lawyer  ·  five agents, one CockroachDB memory  ·  five proofs it changes the outcome",
             color="#f0f6fc", fontsize=19, y=0.985)
out = r"B:\Chronicle\docs\suite_ablations.png"
plt.savefig(out, dpi=120, facecolor="#0d1117", bbox_inches="tight")
print("wrote", out)
