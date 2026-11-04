from nb_builder import md, code, write, SETUP

cells = [
md("""
# 03 · Participação por Categoria e Região (UF / Município)
**Tech Challenge – Fase 1 · POSTECH Data Analytics** · Trilha: *Crescimento e Receita*

**Perguntas de negócio**
1. Quais categorias sustentam a receita e quais estão puxando (ou freando) o crescimento?
2. Onde estão os clientes? Quais regiões estão sub-exploradas em relação ao seu tamanho?

**Dado externo:** população estimada por UF em 2018 (IBGE) para medir a **penetração** do e-commerce –
receita por habitante e pedidos por 100 mil habitantes.
"""),
code(SETUP),
code("""
items = analysis_base()
R = items["price"].sum()
ped = orders_base(items)
print(f"Receita analisada: {brl(R)} | {items['product_category_name'].nunique()} categorias | "
      f"{items['customer_state'].nunique()} UFs | {fmt_int(items.groupby(['customer_city','customer_state']).ngroups)} municípios")
"""),
md("## 1. Categorias: quem sustenta a receita"),
code("""
cat = items.groupby("product_category_name").agg(
    receita=("price", "sum"), pedidos=("order_id", "nunique"),
    itens=("order_item_id", "count"), preco_medio=("price", "mean"),
).sort_values("receita", ascending=False)
cat["participacao"] = cat["receita"] / R
cat["acumulado"] = cat["participacao"].cumsum()
n80 = int((cat["acumulado"] < 0.80).sum() + 1)
print(f"{n80} de {len(cat)} categorias ({n80/len(cat):.0%}) concentram 80% da receita")
print(f"Top 5 categorias = {pct(cat['participacao'].head(5).sum())} da receita")
cat.head(15)
"""),
code("""
top = cat.head(15).iloc[::-1]
fig, ax = plt.subplots(figsize=(11, 6.5))
cores = [COLORS["primary"] if i >= len(top) - 5 else COLORS["secondary"] for i in range(len(top))]
ax.barh(top.index.str.replace("_", " "), top["participacao"], color=cores)
for y, (v, r) in enumerate(zip(top["participacao"], top["receita"])):
    ax.text(v + 0.002, y, f"{pct(v)}  ·  {brl_short(r)}", va="center", fontsize=9)
ax.set_title(f"5 categorias geram 40% da receita; {n80} de {len(cat)} geram 80%")
subtitle(ax, "Participação na receita por categoria (top 15) · jan/2017–ago/2018")
ax.grid(axis="y", visible=False)
ax.grid(axis="x", visible=True)
axis_pct(ax, "x")
ax.set_xlim(0, top["participacao"].max() * 1.35)
save(fig, "07_categorias_participacao")
plt.show()
"""),
md("## 2. Categorias: quem está puxando o crescimento"),
code("""
def receita_periodo(ini, fim):
    p = items[(items["month"] >= ini) & (items["month"] <= fim)]
    return p.groupby("product_category_name")["price"].sum()

g = pd.DataFrame({"jan_ago_17": receita_periodo("2017-01-01", "2017-08-01"),
                  "jan_ago_18": receita_periodo("2018-01-01", "2018-08-01")}).fillna(0)
g["crescimento"] = g["jan_ago_18"] / g["jan_ago_17"] - 1
g["participacao_18"] = g["jan_ago_18"] / g["jan_ago_18"].sum()
g["receita_incremental"] = g["jan_ago_18"] - g["jan_ago_17"]
g["contrib_crescimento"] = g["receita_incremental"] / g["receita_incremental"].sum()
cresc_total = g["jan_ago_18"].sum() / g["jan_ago_17"].sum() - 1
g20 = g.sort_values("jan_ago_18", ascending=False).head(20)
print(f"Crescimento médio da empresa (jan–ago 18 vs 17): {pct(cresc_total)}")
g20[["jan_ago_17", "jan_ago_18", "crescimento", "participacao_18", "contrib_crescimento"]]
"""),
code("""
g15 = g.sort_values("jan_ago_18", ascending=False).head(15).sort_values("crescimento")
fig, ax = plt.subplots(figsize=(11, 6.5))
cores = np.where(g15["crescimento"] > cresc_total, COLORS["primary"], COLORS["accent"])
ax.barh(g15.index.str.replace("_", " "), g15["crescimento"], color=cores)
for y, (v, sh) in enumerate(zip(g15["crescimento"], g15["participacao_18"])):
    ax.text(v + 0.04, y, f"+{v*100:.0f}%  (part. {pct(sh)})", va="center", fontsize=9)
ax.axvline(cresc_total, color=COLORS["dark"], ls="--", lw=1)
ax.text(cresc_total + 0.04, -0.9, f"média Olist +{cresc_total*100:.0f}%", fontsize=9, color=COLORS["dark"])
ax.set_title("Beleza & saúde, relógios e bebês aceleram; cool stuff, brinquedos e perfumaria travaram")
subtitle(ax, "Crescimento da receita jan–ago/18 vs jan–ago/17 · 15 maiores categorias · entre parênteses, participação em 2018")
axis_pct(ax, "x")
ax.set_xlim(0, g15["crescimento"].max() * 1.35)
ax.set_ylim(-1.3, len(g15) - 0.4)
ax.grid(axis="y", visible=False); ax.grid(axis="x", visible=True)
save(fig, "08_categorias_crescimento")
plt.show()
"""),
code("""
contrib = g.sort_values("receita_incremental", ascending=False)
print("Categorias que mais adicionaram receita (jan–ago 18 vs 17):")
for nome, r in contrib.head(5).iterrows():
    print(f"  {nome:<25} +{brl(r['receita_incremental'])}  ({pct(r['contrib_crescimento'])} do crescimento)")
print(f"Top 5 explicam {pct(contrib['contrib_crescimento'].head(5).sum())} do crescimento")
"""),
md("""
**Leitura:**
* **Motores do crescimento:** beleza & saúde (+211%), relógios & presentes (+243%), utilidades domésticas
  (+203%), bebês (+264%) e telefonia (+196%) crescem acima da média. Beleza & saúde e relógios, sozinhas,
  explicam cerca de um quarto da receita incremental.
* **Categorias travadas:** cool stuff (+9%), perfumaria (+43%), brinquedos (+42%) e ferramentas & jardim
  (+49%) crescem bem abaixo da média – perdem relevância no mix e merecem diagnóstico (sortimento, preço,
  sellers).
"""),
md("## 3. Regiões: concentração no Sudeste"),
code("""
uf = items.groupby("customer_state").agg(
    receita=("price", "sum"), frete=("freight_value", "sum"),
    pedidos=("order_id", "nunique"), clientes=("customer_unique_id", "nunique"))
uf["participacao"] = uf["receita"] / R
uf["populacao"] = uf.index.map(IBGE_POP_2018)
uf["regiao"] = uf.index.map(UF_REGIAO)
uf["ticket_medio"] = uf["receita"] / uf["pedidos"]
uf["receita_por_mil_hab"] = uf["receita"] / uf["populacao"] * 1000
uf["pedidos_100k_hab"] = uf["pedidos"] / uf["populacao"] * 1e5
uf["frete_sobre_receita"] = uf["frete"] / uf["receita"]
uf = uf.sort_values("receita", ascending=False)
uf
"""),
code("""
reg = uf.groupby("regiao").agg(receita=("receita", "sum"), frete=("frete", "sum"),
                               pedidos=("pedidos", "sum"), populacao=("populacao", "sum"))
reg["% receita"] = reg["receita"] / reg["receita"].sum()
reg["% população"] = reg["populacao"] / reg["populacao"].sum()
reg["índice de penetração"] = reg["% receita"] / reg["% população"]
reg["ticket_medio"] = reg["receita"] / reg["pedidos"]
reg["receita_por_mil_hab"] = reg["receita"] / reg["populacao"] * 1000
reg["frete_sobre_receita"] = reg["frete"] / reg["receita"]
reg = reg.sort_values("receita", ascending=False)
reg[["% receita", "% população", "índice de penetração", "receita_por_mil_hab", "ticket_medio", "frete_sobre_receita"]]
"""),
code("""
fig, ax = plt.subplots(figsize=(11, 4.8))
x = np.arange(len(reg))
w = 0.38
ax.bar(x - w/2, reg["% população"], w, color=COLORS["neutral"], label="% da população (IBGE 2018)")
ax.bar(x + w/2, reg["% receita"], w, color=COLORS["primary"], label="% da receita Olist")
for i, (p, r) in enumerate(zip(reg["% população"], reg["% receita"])):
    ax.text(i - w/2, p + 0.01, pct(p, 0), ha="center", fontsize=9, color=COLORS["dark"])
    ax.text(i + w/2, r + 0.01, pct(r, 0), ha="center", fontsize=9, color=COLORS["primary"], weight="bold")
ax.set_xticks(x, reg.index)
axis_pct(ax)
ax.legend(loc="upper right")
ax.set_title("Nordeste tem 27% da população, mas gera só 11% da receita")
subtitle(ax, "Participação de cada região na população brasileira vs. na receita da Olist")
save(fig, "09_regioes_populacao_receita")
plt.show()
"""),
md("### Penetração por UF (dado externo IBGE)"),
code("""
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), sharey=True)
u = uf.sort_values("receita_por_mil_hab")
cor_reg = {"Sudeste": COLORS["primary"], "Sul": COLORS["secondary"], "Centro-Oeste": "#7E8FA6",
           "Nordeste": COLORS["accent"], "Norte": "#C9A227"}
c = u["regiao"].map(cor_reg)
ax1.barh(u.index, u["receita_por_mil_hab"], color=c)
ax1.set_title("Receita por mil habitantes (R$)")
ax1.xaxis.set_major_formatter(plt.matplotlib.ticker.FuncFormatter(lambda x, p: f"R$ {x:.0f}"))
ax1.grid(axis="y", visible=False); ax1.grid(axis="x", visible=True)
ax2.barh(u.index, u["frete_sobre_receita"], color=c)
ax2.set_title("Frete como % do valor dos produtos")
axis_pct(ax2, "x")
ax2.grid(axis="y", visible=False); ax2.grid(axis="x", visible=True)
from matplotlib.patches import Patch
fig.legend(handles=[Patch(color=v, label=k) for k, v in cor_reg.items()], loc="lower center",
           ncol=5, bbox_to_anchor=(0.5, -0.03))
fig.suptitle("Onde o frete pesa mais, a Olist vende menos por habitante", x=0.01, ha="left",
             fontsize=15, weight="bold")
fig.tight_layout(rect=(0, 0.03, 1, 1))
save(fig, "10_penetracao_frete_uf")
plt.show()
corr = uf[["receita_por_mil_hab", "frete_sobre_receita"]].corr(method="spearman").iloc[0, 1]
print(f"Correlação (Spearman) entre receita/hab e peso do frete nas 27 UFs: {corr:.2f}")
"""),
md("""
**Leitura:**
* **Concentração:** Sudeste = 65% da receita (só SP = 38%). Sul e Sudeste juntos somam ~80%.
* **Sub-penetração do Norte/Nordeste:** o Nordeste tem 27% da população e apenas 11% da receita
  (índice de penetração ≈ 0,4). A cada mil habitantes, o Sudeste gera R$ 100 de receita (SP: R$ 113); o Nordeste, R$ 27.
* **O frete é a barreira:** no Norte/Nordeste o frete equivale a 20–28% do valor dos produtos, contra 14% em
  SP – e as UFs onde o frete pesa mais são justamente as de menor receita por habitante (correlação
  fortemente negativa). O ticket médio é **maior** nessas regiões: o cliente só compra quando o item é caro
  o suficiente para "compensar" o frete.
"""),
md("## 4. Municípios"),
code("""
cid = items.groupby(["customer_city", "customer_state"]).agg(
    receita=("price", "sum"), pedidos=("order_id", "nunique")).sort_values("receita", ascending=False)
cid["participacao"] = cid["receita"] / R
cid["acumulado"] = cid["participacao"].cumsum()
n_mun = len(cid)
print(f"{fmt_int(n_mun)} municípios com vendas | top 10 = {pct(cid['participacao'].head(10).sum())} da receita | "
      f"municípios para 50% da receita: {(cid['acumulado'] < 0.5).sum() + 1}")
cid.head(10)
"""),
code("""
t10 = cid.head(10).iloc[::-1]
fig, ax = plt.subplots(figsize=(11, 5))
labels = [f"{c.title()} ({u})" for c, u in t10.index]
ax.barh(labels, t10["participacao"], color=[COLORS["accent"] if i >= 8 else COLORS["primary"]
                                           for i in range(len(t10))])
for y, v in enumerate(t10["participacao"]):
    ax.text(v + 0.002, y, pct(v), va="center", fontsize=9)
ax.set_title("São Paulo e Rio respondem por 21% da receita; top 10 cidades por 34%")
subtitle(ax, "Participação na receita – 10 maiores municípios compradores")
axis_pct(ax, "x")
ax.grid(axis="y", visible=False); ax.grid(axis="x", visible=True)
save(fig, "11_municipios_top10")
plt.show()
"""),
md("## 5. Crescimento por região"),
code("""
rg = pd.DataFrame({
    "jan_ago_17": items[(items["month"] >= "2017-01-01") & (items["month"] <= "2017-08-01")].groupby("customer_region")["price"].sum(),
    "jan_ago_18": items[(items["month"] >= "2018-01-01") & (items["month"] <= "2018-08-01")].groupby("customer_region")["price"].sum(),
})
rg["crescimento"] = rg["jan_ago_18"] / rg["jan_ago_17"] - 1
rg.sort_values("crescimento", ascending=False)
"""),
md("""
## Conclusões do notebook
1. **Mix concentrado:** 5 categorias = 40% da receita; 18 de 74 = 80%.
2. **Motores:** beleza & saúde, relógios & presentes, utilidades domésticas e bebês crescem 2–3x a média.
   **Travadas:** cool stuff, perfumaria, brinquedos e ferramentas & jardim.
3. **Geografia concentrada:** Sudeste 65% da receita; São Paulo (capital) sozinha 14%.
4. **Concentração aumentando:** o Sudeste cresceu +149% (jan–ago 18 vs 17), acima de Nordeste (+119%) e
   Norte (+71%) – a dependência do eixo SP-RJ-MG está aumentando, não diminuindo.
5. **Oportunidade regional:** Norte/Nordeste têm 36% da população e 14% da receita; o frete
   (20–28% do valor do produto) é a principal barreira – espaço para logística regional e sellers locais.

➡️ Próximo: `04_top_performers.ipynb`
"""),
]

write("notebooks/03_categorias_e_regioes.ipynb", cells)
