"""Gera os gráficos do README a partir dos CSVs exportados pelos workflows KNIME (Olist_KNIME_Portfolio/data/processed/).

Uso: python docs/img/gerar_graficos.py   (a partir da raiz do projeto)
Requer apenas matplotlib (stdlib csv para leitura).
"""
import csv
import textwrap
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.environ.get("TMPDIR", "/tmp"), "mpl"))
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
OUT = RAIZ / "Olist_KNIME_Portfolio" / "data" / "processed"
IMG = Path(__file__).resolve().parent

ACENTO = "#C2410C"      # laranja queimado
CINZA = "#9CA3AF"
CINZA_ESC = "#374151"
CINZA_CLARO = "#D1D5DB"
FONTE = "Fonte: Olist (Kaggle) · análise em KNIME"

plt.rcParams.update({
    "figure.figsize": (10.67, 6), "figure.dpi": 150, "savefig.dpi": 150,
    "font.size": 12, "axes.titlesize": 17, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.titlepad": 28,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": CINZA, "axes.labelcolor": CINZA_ESC,
    "xtick.color": CINZA_ESC, "ytick.color": CINZA_ESC,
    "text.color": CINZA_ESC,
})


def ler(nome):
    with open(OUT / nome, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def br(x, casas=1):
    s = f"{x:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x, casas=1):
    return br(100 * x, casas) + "%"


def subtitulo(ax, texto):
    ax.text(0, 1.02, texto, transform=ax.transAxes, fontsize=12, color="#6B7280", va="bottom")


def salvar(fig, nome, nota=None):
    rodape = FONTE if not nota else f"{nota}\n{FONTE}"
    fig.text(0.01, 0.01, rodape, fontsize=9, color="#6B7280", ha="left", va="bottom")
    fig.savefig(IMG / nome, bbox_inches=None)
    plt.close(fig)
    print("ok", nome)


# 01 — nota por faixa de entrega -------------------------------------------
def g01():
    d = ler("painel_faixa_entrega.csv")
    rot = [textwrap.fill(r["faixa_entrega"].split(") ", 1)[-1], 10) for r in d]
    ruim = [float(r["taxa_avaliacao_ruim"]) for r in d]
    nota = [float(r["nota_media"]) for r in d]
    atraso = [float(r["taxa_atraso"]) > 0 for r in d]
    fig, ax = plt.subplots()
    fig.subplots_adjust(left=0.07, right=0.98, top=0.82, bottom=0.22)
    cores = [ACENTO if a else CINZA for a in atraso]
    bars = ax.bar(rot, ruim, color=cores, width=0.65)
    for b, v, n in zip(bars, ruim, nota):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.012, pct(v), ha="center", fontsize=12,
                fontweight="bold", color=CINZA_ESC)
        ax.text(b.get_x() + b.get_width() / 2, -0.155, f"nota média {br(n, 2)}", ha="center",
                fontsize=10, color="#6B7280", transform=ax.get_xaxis_transform())
    ax.set_ylim(0, 0.9)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pct(v, 0)))
    ax.set_ylabel("% de avaliações ruins (nota 1–2)")
    ax.tick_params(axis="x", length=0, pad=4)
    ax.set_title("Atrasou, a nota despenca")
    subtitulo(ax, f"Avaliações ruins: {pct(ruim[0])} quando chega 15+ dias antes vs. "
                  f"{pct(ruim[-1])} com 8+ dias de atraso")
    salvar(fig, "01_nota_por_faixa_entrega.png",
           "Entrega real vs. data prometida. Laranja = pedidos atrasados.")
    return ruim[-1], ruim[0]


# 02 — atraso por UF --------------------------------------------------------
def g02():
    d = [r for r in ler("painel_uf.csv") if int(r["pedidos"]) >= 300]
    d.sort(key=lambda r: float(r["taxa_atraso"]))
    uf = [r["customer_state"] for r in d]
    tx = [float(r["taxa_atraso"]) for r in d]
    top = set(sorted(uf, key=lambda u: -tx[uf.index(u)])[:5])
    fig, ax = plt.subplots()
    fig.subplots_adjust(left=0.06, right=0.97, top=0.85, bottom=0.15)
    bars = ax.barh(uf, tx, color=[ACENTO if u in top else CINZA_CLARO for u in uf], height=0.7)
    for b, v, u in zip(bars, tx, uf):
        ax.text(v + 0.002, b.get_y() + b.get_height() / 2, pct(v), va="center", fontsize=9,
                color=CINZA_ESC, fontweight="bold" if u in top else "normal")
    ax.tick_params(axis="y", length=0, labelsize=9)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pct(v, 0)))
    ax.set_xlim(0, max(tx) * 1.12)
    ax.set_xlabel("% de pedidos entregues após a data prometida")
    ax.spines["left"].set_visible(False)
    kpi = float(ler("painel_kpis.csv")[0]["taxa_atraso"])
    ax.axvline(kpi, color=CINZA_ESC, lw=1, ls="--", zorder=0, alpha=0.6)
    ax.text(kpi + 0.002, 0.2, f"média Brasil {pct(kpi)}", fontsize=9, color=CINZA_ESC)
    ax.set_title("Nordeste lidera os atrasos")
    subtitulo(ax, f"{uf[-1]} atrasa {pct(tx[-1])} dos pedidos — {br(tx[-1] / kpi, 1)}x a média nacional")
    salvar(fig, "02_atraso_por_uf.png", "Apenas UFs com ≥ 300 pedidos. Destaque: 5 maiores taxas.")
    return uf[-1], tx[-1]


# 03 — pedidos por mês -----------------------------------------------------
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def g03():
    d = [r for r in ler("painel_mes.csv") if "2017-01" <= r["purchase_month"] <= "2018-08"]
    m = [r["purchase_month"] for r in d]
    p = [int(r["pedidos"]) for r in d]
    rot = [f"{MESES[int(x[5:]) - 1]}\n{x[:4]}" if x[5:] == "01" or i == 0 else MESES[int(x[5:]) - 1]
           for i, x in enumerate(m)]
    fig, ax = plt.subplots()
    fig.subplots_adjust(left=0.08, right=0.97, top=0.82, bottom=0.17)
    x = range(len(m))
    ax.plot(x, p, color=CINZA_ESC, lw=2.2, marker="o", ms=4)
    i = m.index("2017-11")
    ax.plot(i, p[i], "o", color=ACENTO, ms=11, zorder=5)
    ax.annotate(f"Black Friday\nnov/2017: {br(p[i], 0)} pedidos\n(+{pct(p[i] / p[i - 1] - 1, 0)} vs. out)",
                xy=(i, p[i]), xytext=(i - 6.3, p[i] - 300), color=ACENTO, fontsize=11,
                fontweight="bold", arrowprops=dict(arrowstyle="->", color=ACENTO, lw=1.3))
    ax.set_xticks(list(x))
    ax.set_xticklabels(rot, fontsize=9)
    ax.set_ylim(0, max(p) * 1.15)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: br(v, 0)))
    ax.set_ylabel("Pedidos entregues por mês de compra")
    ax.grid(axis="y", color="#E5E7EB", lw=0.8)
    ax.set_axisbelow(True)
    ax.set_title("Black Friday 2017 foi o pico do período")
    subtitulo(ax, f"Volume mensal saiu de {br(p[0], 0)} (jan/2017) para {br(p[-1], 0)} (ago/2018)")
    salvar(fig, "03_pedidos_por_mes.png", "Meses com poucos pedidos (2016 e após ago/2018) excluídos.")
    return p[i]


# 04 — receita por segmento RFM --------------------------------------------
def g04():
    d = ler("rfm_perfil_segmentos.csv")
    d.sort(key=lambda r: -float(r["receita_total"]))
    seg = [r["segmento"] for r in d]
    rec = [float(r["receita_total"]) for r in d]
    cli = [int(r["clientes"]) for r in d]
    tr, tc = sum(rec), sum(cli)
    fig, ax = plt.subplots()
    fig.subplots_adjust(left=0.11, right=0.98, top=0.82, bottom=0.2)
    cores = [ACENTO if i == 0 else CINZA for i in range(len(seg))]
    bars = ax.bar(range(len(seg)), rec, color=cores, width=0.62)
    for b, r, c in zip(bars, rec, cli):
        ax.text(b.get_x() + b.get_width() / 2, r + tr * 0.008, f"{pct(r / tr)} da receita",
                ha="center", fontsize=11, fontweight="bold")
        ax.text(b.get_x() + b.get_width() / 2, r + tr * 0.035, f"{pct(c / tc)} dos clientes",
                ha="center", fontsize=10, color="#6B7280")
    ax.set_xticks(range(len(seg)))
    ax.set_xticklabels([s.replace(" (", "\n(").replace(" de ", "\nde ", 1) if len(s) > 14 else s
                        for s in seg], fontsize=11)
    ax.tick_params(axis="x", length=0)
    ax.set_ylim(0, max(rec) * 1.25)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "R$ " + br(v / 1e6, 0) + " mi"))
    ax.set_ylabel("Receita total")
    ax.set_title("Clientes recentes de alto valor concentram a receita")
    s1 = rec[0] / tr
    s2 = (rec[0] + rec[1]) / tr
    subtitulo(ax, f"Os 2 segmentos de alto valor somam {pct(s2)} da receita com "
                  f"{pct((cli[0] + cli[1]) / tc)} dos clientes")
    salvar(fig, "04_receita_por_segmento.png", "Segmentação RFM por cliente único.")
    return s1, s2


# 05 — importância de variáveis --------------------------------------------
NOMES = {
    "delay_days": "Dias de atraso", "delivery_days": "Dias até entregar",
    "customer_state": "UF do cliente", "delivery_status": "Atrasou? (sim/não)",
    "n_items": "Nº de itens", "n_sellers": "Nº de vendedores", "freight_value": "Valor do frete",
    "product_weight_g": "Peso do produto", "freight_ratio": "Frete / valor",
    "items_value": "Valor dos itens", "product_photos_qty": "Nº de fotos",
    "same_state": "Vendedor na mesma UF", "payment_type": "Forma de pagamento",
    "installments": "Parcelas",
}
ENTREGA = {"delay_days", "delivery_days", "delivery_status"}


def g05():
    d = ler("rf_importancia_variaveis.csv")
    d.sort(key=lambda r: float(r["importancia_proxy"]))
    var = [r["row ID"] for r in d]
    imp = [float(r["importancia_proxy"]) for r in d]
    fig, ax = plt.subplots()
    fig.subplots_adjust(left=0.22, right=0.96, top=0.83, bottom=0.12)
    bars = ax.barh([NOMES.get(v, v) for v in var], imp,
                   color=[ACENTO if v in ENTREGA else CINZA for v in var], height=0.68)
    for b, v in zip(bars, imp):
        ax.text(v + 0.008, b.get_y() + b.get_height() / 2, br(v, 2), va="center", fontsize=10)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, max(imp) * 1.12)
    ax.set_xlabel("Importância (splits ÷ candidatos, níveis 0–2 da Random Forest)")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: br(v, 1)))
    ax.set_title("Sem vazamento, nenhuma variável sozinha domina")
    subtitulo(ax, "Laranja = variáveis de entrega. Importância aproximada (splits ÷ candidatos)")
    salvar(fig, "05_importancia_variaveis.png")
    return NOMES[var[-1]], imp[-1]


# 06 — comparação de modelos -----------------------------------------------
def metricas(nome):
    rows = ler(nome)
    ruim = rows[1]
    return {"Recall": float(ruim["Recall"]), "Precisão": float(ruim["Precision"]),
            "F1": float(ruim["F-measure"]), "Kappa": float(rows[-1]["Cohen's kappa"])}


def g06():
    modelos = [("Baseline\n(\"atrasou = ruim\")", "metricas_baseline.csv", "#D1D5DB"),
               ("Árvore de decisão", "metricas_arvore.csv", "#6B7280"),
               ("Random Forest\n(limiar 0,12)", "metricas_random_forest.csv", ACENTO)]
    met = ["Recall", "Precisão", "F1", "Kappa"]
    vals = [metricas(f) for _, f, _ in modelos]
    fig, ax = plt.subplots()
    fig.subplots_adjust(left=0.07, right=0.98, top=0.82, bottom=0.17)
    w = 0.26
    for j, ((nome, _, cor), v) in enumerate(zip(modelos, vals)):
        xs = [i + (j - 1) * w for i in range(len(met))]
        ys = [v[m] for m in met]
        bars = ax.bar(xs, ys, w * 0.92, color=cor, label=nome.replace("\n", " "))
        for b, y in zip(bars, ys):
            ax.text(b.get_x() + b.get_width() / 2, y + 0.012, br(y, 2), ha="center", fontsize=10,
                    fontweight="bold" if cor == ACENTO else "normal")
    ax.set_xticks(range(len(met)))
    ax.set_xticklabels(["Recall\n(classe ruim)", "Precisão\n(classe ruim)", "F1\n(classe ruim)",
                        "Kappa de Cohen\n(geral)"])
    ax.tick_params(axis="x", length=0)
    ax.set_ylim(0, 0.65)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: br(v, 1)))
    ax.legend(frameon=False, loc="upper right", ncol=3, fontsize=10)
    rf, bl = vals[2], vals[0]
    ax.set_title("Random Forest acha 8x mais avaliações ruins que a regra simples")
    subtitulo(ax, f"Recall da classe ruim: {pct(rf['Recall'])} (RF) vs. {pct(bl['Recall'])} (baseline); "
                  f"kappa {br(rf['Kappa'], 2)} vs. {br(bl['Kappa'], 2)}")
    salvar(fig, "06_comparacao_modelos.png", "Conjunto de teste. Classe positiva = avaliação ruim (nota 1–2).")
    return rf, bl


# 07 — vendedores por pedido -----------------------------------------------
def g07():
    d = ler("painel_vendedores_por_pedido.csv")
    grupos = {"1": [0, 0.0], "2": [0, 0.0], "3+": [0, 0.0]}
    for r in d:
        k = r["n_sellers"] if int(r["n_sellers"]) < 3 else "3+"
        n = int(r["pedidos"])
        grupos[k][0] += n
        grupos[k][1] += n * float(r["taxa_avaliacao_ruim"])
    rot = list(grupos)
    ped = [grupos[k][0] for k in rot]
    tx = [grupos[k][1] / grupos[k][0] for k in rot]
    fig, ax = plt.subplots()
    fig.subplots_adjust(left=0.08, right=0.98, top=0.82, bottom=0.15)
    bars = ax.bar([f"{k} vendedor" + ("" if k == "1" else "es") for k in rot], tx,
                  color=[CINZA, ACENTO, ACENTO], width=0.55)
    for b, v, n in zip(bars, tx, ped):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.012, pct(v), ha="center", fontsize=14,
                fontweight="bold")
        ax.text(b.get_x() + b.get_width() / 2, v / 2, f"{br(n, 0)}\npedidos", ha="center",
                va="center", fontsize=10, color="white" if v > 0.2 else CINZA_ESC)
    ax.set_ylim(0, max(tx) * 1.18)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: pct(v, 0)))
    ax.set_ylabel("% de avaliações ruins (nota 1–2)")
    ax.tick_params(axis="x", length=0, labelsize=12)
    ax.set_title("Pedido com mais de um vendedor vira reclamação")
    subtitulo(ax, f"Com 2 vendedores, {pct(tx[1])} de avaliações ruins — {br(tx[1] / tx[0], 1)}x "
                  f"o pedido de vendedor único ({pct(tx[0])})")
    salvar(fig, "07_vendedores_por_pedido.png",
           "Nº de vendedores distintos no pedido. \"3+\" agrega 3, 4 e 5 vendedores (taxa ponderada por pedidos).")
    return tx, ped


# 08 — avaliação antes da entrega ------------------------------------------
def g08():
    d = [r for r in ler("olist_pedidos.csv") if r["review_class"] in ("ruim", "boa")]
    grupos = {}
    for r in d:
        g = "Atrasados" if int(r["delay_days"]) > 0 else "No prazo"
        quando = "antes" if r["review_date"] < r["delivered_date"] else "depois"
        c = grupos.setdefault(g, {"antes": [0, 0], "depois": [0, 0]})
        c[quando][0] += 1
        c[quando][1] += r["review_class"] == "ruim"
    ordem = ["No prazo", "Atrasados"]
    fig, ax = plt.subplots()
    fig.subplots_adjust(left=0.13, right=0.97, top=0.80, bottom=0.20)
    for i, g in enumerate(ordem):
        tot = sum(v[0] for v in grupos[g].values())
        esq = 0
        for quando, cor in (("antes", ACENTO), ("depois", CINZA_CLARO)):
            n, ruim = grupos[g][quando]
            w = n / tot
            ax.barh(i, w, left=esq, color=cor, height=0.55,
                    label=("Avaliou antes de receber" if quando == "antes" else "Avaliou depois de receber") if i == 0 else None)
            if w > 0.06:
                txt = f"{pct(w, 1 if w > 0.99 else 0)} dos pedidos\n{pct(ruim / n, 0)} ruins"
                ax.text(esq + w / 2, i, txt, ha="center", va="center", fontsize=11, fontweight="bold",
                        color="white" if cor == ACENTO else CINZA_ESC)
            elif n:
                ax.text(esq + w + 0.01, i + 0.36, f"{pct(w, 1)} antes ({pct(ruim / n, 0)} ruins)",
                        ha="left", va="center", fontsize=10, color=ACENTO)
            esq += w
        ax.text(-0.012, i - 0.2, f"{br(tot, 0)} pedidos", ha="right", va="center", fontsize=9, color="#6B7280")
    ax.set_yticks([i + 0.06 for i in range(len(ordem))])
    ax.set_yticklabels(ordem, fontsize=13)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: pct(v, 0)))
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=2, fontsize=10)
    at = grupos["Atrasados"]
    tot_at = at["antes"][0] + at["depois"][0]
    ax.set_title("Quem recebe com atraso avalia antes de o produto chegar")
    subtitulo(ax, f"{pct(at['antes'][0] / tot_at, 0)} dos atrasados foram avaliados antes da entrega "
                  f"({pct(at['antes'][1] / at['antes'][0], 0)} ruins); depois de receber: "
                  f"{pct(at['depois'][1] / at['depois'][0], 0)}")
    salvar(fig, "08_avaliacao_antes_da_entrega.png",
           "Pedidos entregues e avaliados. \"Antes\" = data de criação da avaliação anterior à data de entrega.")
    return grupos


if __name__ == "__main__":
    print(g01(), g02(), g03(), g04(), g05(), g06(), g07(), g08(), sep="\n")
