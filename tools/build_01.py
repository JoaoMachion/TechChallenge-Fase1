from nb_builder import md, code, write, SETUP

cells = [
md("""
# 01 · Qualidade e Preparação dos Dados
**Tech Challenge – Fase 1 · POSTECH Data Analytics** · Trilha: *Crescimento e Receita*

**Objetivo deste notebook:** garantir que os números apresentados aos investidores sejam confiáveis.
Aqui fazemos o inventário das tabelas, checamos a integridade das chaves e dos valores, documentamos as regras
de negócio adotadas e geramos a base analítica usada nos notebooks seguintes.

| Etapa | O que verificamos |
|---|---|
| 1. Inventário | Linhas, colunas e valores ausentes de cada tabela |
| 2. Integridade | Chaves duplicadas e relacionamentos órfãos entre tabelas |
| 3. Consistência | Preços/fretes negativos, datas fora de ordem, status dos pedidos |
| 4. Recorte temporal | Escolha da janela de análise com meses completos |
| 5. Base analítica | Tabela única no grão item de pedido, salva em `data/processed/` |
"""),
code(SETUP),
md("## 1. Inventário das tabelas"),
code("""
t = load_all()
inv = pd.DataFrame({
    "linhas": {k: len(v) for k, v in t.items()},
    "colunas": {k: v.shape[1] for k, v in t.items()},
    "células_nulas_%": {k: v.isna().mean().mean() * 100 for k, v in t.items()},
})
inv
"""),
code("""
# Colunas com valores ausentes (apenas as que têm algum nulo)
nulos = []
for nome, df in t.items():
    s = df.isna().mean()
    for col, v in s[s > 0].items():
        nulos.append((nome, col, v * 100))
pd.DataFrame(nulos, columns=["tabela", "coluna", "% nulos"]).sort_values("% nulos", ascending=False)
"""),
md("""
**Leitura:** os nulos se concentram em (i) datas de entrega/aprovação – esperados para pedidos ainda não
entregues ou cancelados; (ii) comentários de avaliação – opcionais para o cliente; (iii) atributos de produto
(categoria, medidas) em ~1,9% dos produtos. Nenhuma coluna usada no cálculo de **receita** (`price`) ou de
**pedidos** (`order_id`) tem nulos.
"""),
md("## 2. Integridade das chaves"),
code("""
checks = {
    "orders.order_id duplicado": t["orders"]["order_id"].duplicated().sum(),
    "customers.customer_id duplicado": t["customers"]["customer_id"].duplicated().sum(),
    "products.product_id duplicado": t["products"]["product_id"].duplicated().sum(),
    "sellers.seller_id duplicado": t["sellers"]["seller_id"].duplicated().sum(),
    "items (order_id, item_id) duplicado": t["order_items"].duplicated(["order_id", "order_item_id"]).sum(),
    "items sem pedido correspondente": (~t["order_items"]["order_id"].isin(t["orders"]["order_id"])).sum(),
    "items com produto inexistente": (~t["order_items"]["product_id"].isin(t["products"]["product_id"])).sum(),
    "items com seller inexistente": (~t["order_items"]["seller_id"].isin(t["sellers"]["seller_id"])).sum(),
    "pedidos com cliente inexistente": (~t["orders"]["customer_id"].isin(t["customers"]["customer_id"])).sum(),
    "pedidos sem nenhum item": (~t["orders"]["order_id"].isin(t["order_items"]["order_id"])).sum(),
    "categorias sem tradução": len(set(t["products"]["product_category_name"].dropna())
                                   - set(t["category_translation"]["product_category_name"])),
}
pd.Series(checks, name="ocorrências").to_frame()
"""),
md("""
**Leitura:** as chaves primárias são únicas e não existem itens "órfãos". Há 775 pedidos sem itens
(praticamente todos cancelados/indisponíveis) – eles não geram receita e ficam fora da base. Duas categorias
não têm tradução para inglês; mantemos o nome em português (usado em toda a análise).

> **Atenção ao identificador de cliente:** `customer_id` é gerado **a cada pedido**. Para contar clientes
> reais usamos `customer_unique_id`.
"""),
code("""
c = t["customers"]
print(f"customer_id distintos:        {c['customer_id'].nunique():>7,}")
print(f"customer_unique_id distintos: {c['customer_unique_id'].nunique():>7,}")
"""),
md("## 3. Consistência de valores e datas"),
code("""
it = t["order_items"]
o = t["orders"]
cons = {
    "itens com preço <= 0": (it["price"] <= 0).sum(),
    "itens com frete < 0": (it["freight_value"] < 0).sum(),
    "itens com frete = 0 (frete grátis)": (it["freight_value"] == 0).sum(),
    "aprovação antes da compra": (o["order_approved_at"] < o["order_purchase_timestamp"]).sum(),
    "entrega ao cliente antes da compra": (o["order_delivered_customer_date"] < o["order_purchase_timestamp"]).sum(),
    "status 'delivered' sem data de entrega": ((o["order_status"] == "delivered") & o["order_delivered_customer_date"].isna()).sum(),
}
display(pd.Series(cons, name="ocorrências").to_frame())
it[["price", "freight_value"]].describe(percentiles=[.01, .25, .5, .75, .99]).T
"""),
md("""
**Leitura:** não há preços negativos/zerados nem datas de entrega anteriores à compra. Os preços têm
cauda longa (mediana ≈ R$ 75, p99 ≈ R$ 890, máximo R$ 6.735), compatível com um marketplace com itens de
alto valor (relógios, informática, móveis). **Não removemos outliers de preço**: são vendas reais e
fazem parte da receita.
"""),
code("""
st = o["order_status"].value_counts().to_frame("pedidos")
st["%"] = st["pedidos"] / st["pedidos"].sum() * 100
st
"""),
md("""
**Regra de negócio – pedidos válidos:** excluímos `canceled` e `unavailable` (≈ 1,2% dos pedidos), pois não
geraram venda. Os demais status (entregue, enviado, faturado, em processamento) representam vendas
efetivadas no momento da extração e entram na receita.
"""),
md("## 4. Recorte temporal"),
code("""
mensal = o.groupby(o["order_purchase_timestamp"].dt.to_period("M")).size()
fig, ax = plt.subplots(figsize=(11, 4))
cores = [COLORS["primary"] if (str(p) >= "2017-01" and str(p) <= "2018-08") else COLORS["neutral"]
         for p in mensal.index]
ax.bar(mensal.index.astype(str), mensal.values, color=cores)
ax.set_title("Janela de análise: jan/2017 a ago/2018 (20 meses completos)")
subtitle(ax, "Pedidos por mês de compra · em cinza, meses excluídos por volume não representativo")
ax.tick_params(axis="x", rotation=90)
axis_int(ax)
save(fig, "00_janela_analise")
plt.show()
"""),
md("""
**Decisão:** analisamos **jan/2017 a ago/2018**.
* 2016 tem apenas ~330 pedidos (fase de testes da operação, com um mês sem vendas).
* set e out/2018 têm 20 pedidos no total – a extração foi cortada, não é queda real de vendas.

Incluir esses meses distorceria crescimento e previsões.
"""),
md("## 5. Base analítica"),
code("""
base = build_items_base(t)
analise = base[base["is_valid"] & base["in_period"]]

resumo = pd.Series({
    "itens (base completa)": len(base),
    "itens na análise": len(analise),
    "pedidos na análise": analise["order_id"].nunique(),
    "clientes únicos": analise["customer_unique_id"].nunique(),
    "sellers ativos": analise["seller_id"].nunique(),
    "produtos vendidos": analise["product_id"].nunique(),
    "categorias": analise["product_category_name"].nunique(),
    "receita (R$, sem frete)": analise["price"].sum(),
    "frete (R$)": analise["freight_value"].sum(),
})
resumo.map(lambda v: f"{v:,.0f}".replace(",", "."))
"""),
code("""
cols = ["order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value",
        "order_status", "order_purchase_timestamp", "month", "customer_unique_id",
        "customer_city", "customer_state", "customer_region", "product_category_name",
        "product_category_name_english", "seller_city", "seller_state", "seller_region"]
out = PROCESSED / "base_itens_analise.csv"
analise[cols].to_csv(out, index=False)
print(f"Base salva em data/processed/{out.name} – {len(analise):,} linhas x {len(cols)} colunas")
"""),
md("""
## Conclusões de qualidade
1. **Dados íntegros:** chaves únicas, sem órfãos, sem valores negativos ou datas incoerentes.
2. **Regras documentadas:** receita = soma de `price` (sem frete) de pedidos não cancelados/indisponíveis;
   clientes contados por `customer_unique_id`; janela jan/2017–ago/2018.
3. **Base única e reproduzível:** todas as regras estão em `src/olist_utils.py` e são reaplicadas
   automaticamente em todos os notebooks.

➡️ Próximo: `02_evolucao_mensal_e_previsao.ipynb`
"""),
]

write("notebooks/01_qualidade_e_preparacao.ipynb", cells)
