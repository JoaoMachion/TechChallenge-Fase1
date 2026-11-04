# Olist E-commerce: Crescimento e Receita
**Tech Challenge, Fase 1, POSTECH Data Analytics (DTAT)**

Relatório executivo para investidores e acionistas, construído a partir do
[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
(cerca de 100 mil pedidos, 2016–2018).

**Trilha analítica escolhida: 1. Crescimento e Receita**
- Evolução mensal de pedidos, receita e ticket médio, com previsão para os 6 meses seguintes
- Participação por categoria e região (UF e município), enriquecida com população do IBGE
- Identificação de produtos e sellers top performers (receita × qualidade)

---

## Principais conclusões

| # | Achado | Evidência |
|---|---|---|
| 1 | **Tração forte, mas a receita entrou em platô em 2018** | Receita jan–ago/18 **+138%** vs jan–ago/17; desde jan/18 está estável em ~R$ 0,9 mi/mês (ago/18 ficou 10% abaixo de jan/18) |
| 2 | **O crescimento veio 100% de volume** | Ticket médio estável em ~R$ 137; pedidos explicam 99,5% do crescimento |
| 3 | **Recompra quase nula** | Só 3% dos clientes compraram mais de uma vez; 97% da receita vem de clientes novos |
| 4 | **Mix concentrado, com motores claros** | 18 de 74 categorias = 80% da receita. Beleza & saúde, relógios, utilidades e bebês crescem 2–3x a média |
| 5 | **Norte/Nordeste sub-explorados por causa do frete** | Nordeste: 27% da população, 11% da receita; frete chega a 20–28% do valor do produto (14% em SP) |
| 6 | **Sellers concentrados e oferta crescendo mais que a demanda** | 10% dos sellers = 67% da receita; sellers ativos +31% em 2018, receita por seller −31% |
| 7 | **Previsão sem novas ações: platô** | R$ 0,86–0,95 mi/mês até fev/2019 (Black Friday ≈ R$ 1,4 mi) |
| 8 | **Potencial das alavancas** | Retenção, expansão N/NE, categorias motor, gestão de sellers e sazonalidade: ~R$ 1,6 mi/ano (+15%) |

---

## Estrutura do repositório

```
.
├── data/
│   ├── raw/                 # CSVs originais do Kaggle (não versionados – ver "Como reproduzir")
│   └── processed/           # base analítica gerada pelo notebook 01 (não versionada)
├── notebooks/
│   ├── 01_qualidade_e_preparacao.ipynb      # inventário, integridade, regras de negócio, base analítica
│   ├── 02_evolucao_mensal_e_previsao.ipynb  # pedidos, receita, ticket, clientes, sazonalidade, previsão
│   ├── 03_categorias_e_regioes.ipynb        # categorias, UF, regiões (IBGE), municípios
│   ├── 04_top_performers.ipynb              # concentração, top produtos, matriz de sellers
│   └── 05_sintese_recomendacoes.ipynb       # KPIs, dimensionamento das alavancas, recomendações
├── reports/
│   └── figures/             # todos os gráficos exportados (usados na apresentação)
├── src/
│   └── olist_utils.py       # carga, regras de negócio, dados IBGE, previsão e padrão visual
├── tools/                   # scripts que geram e executam os notebooks
├── requirements.txt
└── README.md
```

## Como reproduzir

```bash
# 1. Ambiente
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Dados: baixe o dataset no Kaggle e extraia os 9 CSVs em data/raw/
#    https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

# 3. Execute os notebooks em ordem (01 → 05), pelo Jupyter:
jupyter lab
#    ou tudo de uma vez pela linha de comando:
jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb
#    alternativa sem Jupyter (executor próprio incluído no repositório):
python tools/run_notebook.py notebooks/0*.ipynb
```

Os notebooks já estão salvos **com as saídas e os gráficos**, então dá para ler tudo direto no GitHub sem executar nada.

---

## Governança de dados

### Fontes
| Fonte | Uso | Observação |
|---|---|---|
| Olist – Brazilian E-Commerce Public Dataset (Kaggle) | Toda a análise | Dados reais anonimizados; 9 tabelas relacionais |
| IBGE – Estimativas da População residente em 01/07/2018 | Penetração por UF (receita por mil habitantes) | Valores embutidos em `src/olist_utils.py` (`IBGE_POP_2018`) |

### Regras de negócio (aplicadas em todos os notebooks via `src/olist_utils.py`)
| Regra | Definição | Justificativa |
|---|---|---|
| **Receita (GMV)** | Soma de `order_items.price` (valor da mercadoria, **sem frete**) | Frete é repasse logístico; analisado à parte |
| **Pedido válido** | `order_status` diferente de `canceled` e `unavailable` | Não geraram venda (~1,2% dos pedidos) |
| **Período** | Compras de **01/01/2017 a 31/08/2018** | 2016 tem ~330 pedidos (operação em teste); set–out/2018 têm 20 pedidos (extração cortada) |
| **Data de referência** | `order_purchase_timestamp` (data da compra) | Reflete o momento da demanda |
| **Cliente** | `customer_unique_id` | `customer_id` muda a cada pedido |
| **Ticket médio** | Receita ÷ pedidos válidos | |
| **Atraso** | `order_delivered_customer_date` > `order_estimated_delivery_date` | Só para pedidos entregues |
| **Categoria** | `product_category_name` (PT); produtos sem categoria = `sem_categoria` | 1,9% dos produtos sem categoria |

### Qualidade dos dados (notebook 01)
- Chaves primárias únicas; nenhum item órfão (sem pedido, produto ou seller).
- 775 pedidos sem itens (99% cancelados/indisponíveis), que ficam fora da base.
- Nenhum preço ≤ 0, nenhum frete negativo, nenhuma data de entrega anterior à compra.
- Nulos concentrados em comentários de avaliação (opcionais) e datas de entrega de pedidos ainda não entregues.
- Outliers de preço (até R$ 6.735) mantidos: são vendas reais.

### Dicionário de dados (tabelas usadas)
| Tabela | Chave | Colunas principais | Grão |
|---|---|---|---|
| `orders` | `order_id` | `customer_id`, `order_status`, datas de compra/aprovação/postagem/entrega/estimada | 1 linha por pedido |
| `order_items` | `order_id` + `order_item_id` | `product_id`, `seller_id`, `price`, `freight_value`, `shipping_limit_date` | 1 linha por item |
| `customers` | `customer_id` | `customer_unique_id`, `customer_zip_code_prefix`, `customer_city`, `customer_state` | 1 linha por pedido-cliente |
| `products` | `product_id` | `product_category_name`, medidas, peso, nº de fotos | 1 linha por produto |
| `sellers` | `seller_id` | `seller_zip_code_prefix`, `seller_city`, `seller_state` | 1 linha por seller |
| `order_reviews` | `review_id` | `order_id`, `review_score` (1–5), comentário, datas | 1 linha por avaliação |
| `category_translation` | `product_category_name` | `product_category_name_english` | 1 linha por categoria |
| `payments`, `geolocation` | – | Não usadas nesta trilha | – |

**Base analítica** (`data/processed/base_itens_analise.csv`): grão de item de pedido, 111.752 linhas,
com pedido + cliente + produto + seller + região e as regras acima aplicadas.

### Previsão
- Modelos comparados: ingênuo, média móvel de 3 meses e Holt com tendência amortecida (implementação própria em numpy/scipy).
- Validação por backtest com origem móvel (cortes em fev, mar e abr/2018; horizonte de 4 meses).
- Média móvel de 3 meses teve o menor erro médio (MAPE ≈ 9%) e é o cenário base; Holt é o cenário otimista. O efeito Black Friday de 2017 (1,57x) é aplicado a novembro.
- Limitação: só 20 meses de série e uma única Black Friday observada.

### Limitações
- O dataset é uma **amostra** da operação da Olist. Valores absolutos (R$) não representam o faturamento total da empresa; as tendências e proporções são o que importa.
- Associações observadas (ex.: frete × penetração) são correlações, não prova de causalidade.
- O dimensionamento das alavancas (notebook 05) é ilustrativo e depende das premissas explicitadas.

---

## Entregáveis
- Repositório GitHub: este repositório
- Apresentação executiva (storytelling): link no material de entrega
- Vídeo executivo (até 5 min): link no material de entrega
