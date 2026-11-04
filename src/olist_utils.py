"""
Funções utilitárias do Tech Challenge – Fase 1 (POSTECH DTAT)
Case: Brazilian E-Commerce Public Dataset by Olist
Trilha analítica: Crescimento e Receita

Centraliza caminhos, carga dos dados brutos, regras de negócio (definição de
receita, período de análise, status válidos), dados externos (IBGE) e o
padrão visual dos gráficos. Todos os notebooks importam este módulo, o que
garante que as mesmas regras sejam aplicadas em toda a análise
(reprodutibilidade e governança).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "reports" / "figures"
for _p in (PROCESSED, FIGURES):
    _p.mkdir(parents=True, exist_ok=True)

FILES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

DATE_COLS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}

# ---------------------------------------------------------------------------
# Regras de negócio (documentadas no README)
# ---------------------------------------------------------------------------
# Pedidos que NÃO geraram venda efetiva são excluídos das métricas de receita.
INVALID_STATUS = ["canceled", "unavailable"]
# Janela com meses completos e volume representativo. 2016 tem só ~330 pedidos
# (operação em teste) e set-out/2018 têm apenas 20 pedidos (extração cortada).
PERIOD_START = "2017-01-01"
PERIOD_END = "2018-08-31"

# ---------------------------------------------------------------------------
# Dados externos – IBGE
# População residente estimada em 1º/jul/2018 (Estimativas da População –
# IBGE, publicadas no DOU em 29/08/2018). Usada para normalizar receita e
# pedidos por habitante e medir a penetração do e-commerce em cada UF.
# ---------------------------------------------------------------------------
IBGE_POP_2018 = {
    "SP": 45_538_936, "MG": 21_040_662, "RJ": 17_159_960, "BA": 14_812_617,
    "PR": 11_348_937, "RS": 11_329_605, "PE": 9_496_294, "CE": 9_075_649,
    "PA": 8_513_497, "SC": 7_075_494, "MA": 7_035_055, "GO": 6_921_161,
    "AM": 4_080_611, "PB": 3_996_496, "ES": 3_972_388, "RN": 3_479_010,
    "MT": 3_441_998, "AL": 3_322_820, "PI": 3_264_531, "DF": 2_974_703,
    "MS": 2_748_023, "SE": 2_278_308, "RO": 1_757_589, "TO": 1_555_229,
    "AC": 869_265, "AP": 829_494, "RR": 576_568,
}

UF_REGIAO = {
    "AC": "Norte", "AM": "Norte", "AP": "Norte", "PA": "Norte", "RO": "Norte",
    "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MS": "Centro-Oeste",
    "MT": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}

# ---------------------------------------------------------------------------
# Padrão visual
# ---------------------------------------------------------------------------
COLORS = {
    "primary": "#1F4E79",   # azul institucional – série principal
    "accent": "#E8772E",    # laranja – destaque / insight
    "secondary": "#6FA8DC",  # azul claro – série de apoio
    "neutral": "#A0A7B0",   # cinza – contexto
    "dark": "#2B2F36",
    "good": "#2E8B57",
    "bad": "#C0392B",
}


def set_style() -> None:
    """Estilo único e limpo para todos os gráficos (linguagem executiva)."""
    plt.rcParams.update({
        "figure.figsize": (11, 5),
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.axisbelow": True,
        "grid.color": "#E6E8EB",
        "grid.linewidth": 0.8,
        "axes.edgecolor": "#C9CED6",
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlepad": 30,
        "axes.labelcolor": COLORS["dark"],
        "axes.labelsize": 10,
        "xtick.color": "#5B636E",
        "ytick.color": "#5B636E",
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.frameon": False,
        "font.family": "DejaVu Sans",
    })


def brl(x: float, decimals: int = 0) -> str:
    """Formata número como moeda brasileira (R$ 1.234.567)."""
    s = f"{x:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def brl_short(x: float, pos=None) -> str:
    """Formatador compacto para eixos: R$ 1,2 mi / R$ 350 mil."""
    if abs(x) >= 1e6:
        return f"R$ {x/1e6:,.1f} mi".replace(".", ",")
    if abs(x) >= 1e3:
        return f"R$ {x/1e3:,.0f} mil".replace(",", ".")
    return f"R$ {x:,.0f}"


def fmt_int(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def pct(x: float, decimals: int = 1) -> str:
    return f"{x*100:.{decimals}f}%".replace(".", ",")


def axis_brl(ax, axis: str = "y") -> None:
    fmt = mtick.FuncFormatter(brl_short)
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


def axis_int(ax, axis: str = "y") -> None:
    fmt = mtick.FuncFormatter(lambda x, p: fmt_int(x))
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


def axis_pct(ax, axis: str = "y", decimals: int = 0) -> None:
    fmt = mtick.FuncFormatter(lambda x, p: f"{x*100:.{decimals}f}%")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def month_axis(ax, every: int = 2) -> None:
    """Eixo X de datas com meses em português (ex.: mar/17)."""
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=every))
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(
        lambda x, p: (lambda d: f"{MESES_PT[d.month-1]}/{d.strftime('%y')}")(mdates.num2date(x))))


def save(fig, name: str) -> Path:
    """Salva a figura em reports/figures (usada na apresentação)."""
    path = FIGURES / f"{name}.png"
    fig.savefig(path, facecolor="white")
    return path


def subtitle(ax, text: str) -> None:
    """Subtítulo cinza abaixo do título – a 'mensagem' do gráfico."""
    ax.text(0, 1.025, text, transform=ax.transAxes, fontsize=10,
            color="#5B636E", va="bottom")


# ---------------------------------------------------------------------------
# Carga e base analítica
# ---------------------------------------------------------------------------
def load_raw(name: str) -> pd.DataFrame:
    """Lê uma tabela bruta do dataset Olist com as datas já convertidas."""
    path = RAW / FILES[name]
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo {path.name} não encontrado em {RAW}.\n"
            "Baixe o dataset em https://www.kaggle.com/datasets/olistbr/"
            "brazilian-ecommerce e extraia os CSVs em data/raw/."
        )
    return pd.read_csv(path, parse_dates=DATE_COLS.get(name, []))


def load_all() -> dict[str, pd.DataFrame]:
    return {k: load_raw(k) for k in FILES}


def build_items_base(t: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    """
    Base analítica no grão ITEM DE PEDIDO, enriquecida com pedido, cliente,
    produto (categoria em PT e EN) e vendedor.

    Receita (GMV) = soma de `price` dos itens (valor da mercadoria, sem frete).
    O frete (`freight_value`) é mantido em coluna própria.
    """
    if t is None:
        t = load_all()
    orders = t["orders"]
    items = t["order_items"]
    cust = t["customers"]
    prod = t["products"][["product_id", "product_category_name"]]
    trans = t["category_translation"]
    sellers = t["sellers"]

    prod = prod.merge(trans, on="product_category_name", how="left")
    prod["product_category_name"] = prod["product_category_name"].fillna("sem_categoria")
    prod["product_category_name_english"] = (
        prod["product_category_name_english"]
        .fillna(prod["product_category_name"])
    )

    base = (
        items
        .merge(orders, on="order_id", how="left")
        .merge(cust, on="customer_id", how="left")
        .merge(prod, on="product_id", how="left")
        .merge(sellers, on="seller_id", how="left")
    )
    base["month"] = base["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
    base["customer_region"] = base["customer_state"].map(UF_REGIAO)
    base["seller_region"] = base["seller_state"].map(UF_REGIAO)
    base["is_valid"] = ~base["order_status"].isin(INVALID_STATUS)
    base["in_period"] = base["order_purchase_timestamp"].between(
        PERIOD_START, pd.Timestamp(PERIOD_END) + pd.Timedelta(days=1), inclusive="left"
    )
    return base


def analysis_base(t: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    """Itens válidos (sem cancelados/indisponíveis) dentro do período de análise."""
    b = build_items_base(t)
    return b[b["is_valid"] & b["in_period"]].copy()


def orders_base(items: pd.DataFrame) -> pd.DataFrame:
    """Agrega a base de itens no grão PEDIDO."""
    agg = items.groupby("order_id").agg(
        month=("month", "first"),
        purchase=("order_purchase_timestamp", "first"),
        customer_unique_id=("customer_unique_id", "first"),
        customer_state=("customer_state", "first"),
        customer_city=("customer_city", "first"),
        customer_region=("customer_region", "first"),
        revenue=("price", "sum"),
        freight=("freight_value", "sum"),
        n_items=("order_item_id", "count"),
        n_sellers=("seller_id", "nunique"),
    ).reset_index()
    return agg


def monthly_kpis(items: pd.DataFrame) -> pd.DataFrame:
    """Pedidos, receita, ticket médio, clientes e variações por mês."""
    o = orders_base(items)
    m = o.groupby("month").agg(
        pedidos=("order_id", "nunique"),
        receita=("revenue", "sum"),
        frete=("freight", "sum"),
        clientes=("customer_unique_id", "nunique"),
    )
    m["ticket_medio"] = m["receita"] / m["pedidos"]
    m["receita_mom"] = m["receita"].pct_change()
    m["receita_yoy"] = m["receita"].pct_change(12)
    m["pedidos_yoy"] = m["pedidos"].pct_change(12)
    return m


# ---------------------------------------------------------------------------
# Previsão – Holt (suavização exponencial com tendência amortecida)
# Implementação própria (numpy/scipy) para não depender do statsmodels.
# ---------------------------------------------------------------------------
def _holt_fit(y: np.ndarray, alpha: float, beta: float, phi: float):
    level, trend = y[0], y[1] - y[0]
    fitted = np.empty_like(y, dtype=float)
    for t in range(len(y)):
        fitted[t] = level + phi * trend
        new_level = alpha * y[t] + (1 - alpha) * (level + phi * trend)
        trend = beta * (new_level - level) + (1 - beta) * phi * trend
        level = new_level
    return fitted, level, trend


def holt_forecast(series: pd.Series, horizon: int = 6, phi: float | None = None):
    """
    Ajusta Holt com tendência amortecida minimizando o erro quadrático
    um-passo-à-frente. Retorna DataFrame com previsão e intervalo de 80%
    (aprox. normal, com erro crescendo com o horizonte).
    """
    from scipy.optimize import minimize

    y = series.values.astype(float)

    def sse(params):
        a, b, p = params
        f, _, _ = _holt_fit(y, a, b, p)
        return np.sum((y[2:] - f[2:]) ** 2)

    bounds = [(0.05, 0.99), (0.01, 0.99), (0.80, 0.98)]
    x0 = [0.5, 0.1, 0.9]
    if phi is not None:
        bounds[2] = (phi, phi)
        x0[2] = phi
    res = minimize(sse, x0=x0, bounds=bounds, method="L-BFGS-B")
    a, b, p = res.x
    fitted, level, trend = _holt_fit(y, a, b, p)
    resid = y[2:] - fitted[2:]
    sigma = resid.std(ddof=1)

    idx = pd.date_range(series.index[-1] + pd.offsets.MonthBegin(1),
                        periods=horizon, freq="MS")
    fc, damp = [], 0.0
    for h in range(1, horizon + 1):
        damp += p ** h
        fc.append(level + damp * trend)
    fc = np.array(fc)
    z80 = 1.2816
    se = sigma * np.sqrt(np.arange(1, horizon + 1))
    out = pd.DataFrame({"previsao": fc, "lim_inf_80": fc - z80 * se,
                        "lim_sup_80": fc + z80 * se}, index=idx)
    params = {"alpha": a, "beta": b, "phi": p, "sigma": sigma,
              "mape_in_sample": float(np.mean(np.abs(resid / y[2:])))}
    return out, pd.Series(fitted, index=series.index), params


def gini(values) -> float:
    """Índice de Gini (0 = receita igualmente distribuída; 1 = concentrada)."""
    x = np.sort(np.asarray(values, dtype=float))
    n = len(x)
    if n == 0 or x.sum() == 0:
        return 0.0
    cum = np.cumsum(x)
    return float((n + 1 - 2 * np.sum(cum) / cum[-1]) / n)
