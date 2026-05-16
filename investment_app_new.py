"""
Анализ инвестиционных проектов
Запуск: streamlit run investment_app.py
Зависимости: pip install streamlit pandas plotly
"""

import streamlit as st #основа веб интерфейса
import pandas as pd #для работы с табличными данными (загрузка, группировка и анализ данных)
import plotly.graph_objects as go #для создания интерактивных графиков (низкоуровневый интерфейс)
import plotly.express as px #высокоуровый интерфйес обёртка для прошлой библиотеки

def _n(value, decimals=0):
    """Format number using space as thousands separator."""
    try:
        s = f"{abs(value):,.{decimals}f}".replace(",", " ")
        return ("-" if value < 0 else "") + s
    except Exception:
        return str(value)


try:
    import pulp #импорт библиотеки PuLP для линейного программирования
    PULP_AVAILABLE = True
except ImportError:
    PULP_AVAILABLE = False

# ─────────────────────────────────────────────
# Конфигурация страницы
# ─────────────────────────────────────────────
st.set_page_config( #название вкладки
    page_title="Инвестиционный анализ",
    page_icon="📋",
    layout="wide", #сайт во всю ширь
)

# ─────────────────────────────────────────────
# Стили #внедрение CSS через markdown
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500;600&display=swap');

    :root {
        --bg-page:       #faf6ee;
        --bg-card:       #f5f0e6;
        --bg-sidebar:    #f0ead8;
        --accent-navy:   #1e3a5f;
        --accent-warm:   #c8773a;
        --accent-mid:    #4a6fa5;
        --text-main:     #1a1a2e;
        --text-muted:    #5a5870;
        --border:        #d8d0bc;
        --ok-bg:         #e6f0e8;
        --ok-text:       #1a4a2a;
        --bad-bg:        #f5e8e4;
        --bad-text:      #6a1f1f;
    }

    /* Шрифт — точечно по контентным элементам, не трогая служебные */
    body, button, input, select, textarea,
    h1, h2, h3, h4, h5, h6, p, label, caption,
    [data-testid="stMarkdownContainer"] *,
    [data-testid="stText"],
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"],
    [data-testid="stDataFrame"],
    [data-testid="stSelectbox"] *,
    [data-testid="stNumberInput"] *,
    [data-testid="stTextInput"] *,
    [data-testid="stSlider"] *,
    [data-testid="stButton"] *,
    [data-testid="stTabs"] [data-baseweb="tab"] *,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] > div *,
    .project-card, .advice-box, .criterion-row,
    .formula-box, .section-header, .badge-ok, .badge-bad {
        font-family: 'Fira Code', monospace !important;
    }
    /* Явно сбрасываем шрифт иконок стрелок чтобы не ломались */
    [data-testid="stExpander"] summary svg,
    [data-testid="stExpander"] summary svg *,
    [data-testid="stExpanderToggleIcon"],
    [data-testid="stExpanderToggleIcon"] * {
        font-family: inherit;
    }
    /* Скрываем артефакт .arrow_down который наползает на текст */
    [data-testid="stExpander"] summary::before,
    [data-testid="stExpander"] summary::after {
        display: none !important;
    }
    /* Expander summary — выравнивание чтобы иконка не перекрывала текст */
    [data-testid="stExpander"] summary {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }
    [data-testid="stExpander"] summary > * {
        position: static !important;
    }

    /* Фон приложения — сливочный */
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="block-container"],
    .stApp {
        background-color: var(--bg-page) !important;
    }

    /* Боковая панель */
    [data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
    }

    /* Скрыть переключатель темы и меню настроек */
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    #MainMenu,
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* Заголовки */
    h1, h2, h3 {
        color: var(--accent-navy) !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em;
    }

    /* Вкладки */
    [data-testid="stTabs"] [data-baseweb="tab"] {
        font-family: 'Fira Code', monospace !important;
        font-weight: 500;
        font-size: 0.78rem;
        letter-spacing: 0.04em;
        color: var(--text-muted);
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        color: var(--accent-navy) !important;
        border-bottom-color: var(--accent-warm) !important;
    }

    /* Карточки проектов */
    .project-card {
        background: var(--bg-card);
        border-left: 3px solid var(--accent-warm);
        border-top: 1px solid var(--border);
        border-bottom: 1px solid var(--border);
        border-right: 1px solid var(--border);
        border-radius: 3px;
        padding: 13px 18px;
        margin-bottom: 12px;
        font-family: 'Fira Code', monospace !important;
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--accent-navy);
    }

    /* Блоки советов */
    .advice-box {
        background: #fdf0df;
        border-left: 3px solid var(--accent-warm);
        border-radius: 3px;
        padding: 13px 17px;
        margin-top: 8px;
        margin-bottom: 14px;
        font-size: 0.88rem;
        line-height: 1.7;
        font-family: 'Fira Code', monospace !important;
        color: var(--text-main);
    }
    .advice-box.good {
        background: #e8f2e8;
        border-left-color: #2a6e40;
    }

    /* Строки критериев */
    .criterion-row {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 7px 0;
        border-bottom: 1px solid var(--border);
        font-size: 0.87rem;
        font-family: 'Fira Code', monospace !important;
    }
    .badge-ok {
        background: var(--ok-bg);
        color: var(--ok-text);
        padding: 2px 10px;
        border-radius: 2px;
        font-weight: 600;
        font-size: 0.74rem;
        letter-spacing: 0.04em;
        font-family: 'Fira Code', monospace !important;
    }
    .badge-bad {
        background: var(--bad-bg);
        color: var(--bad-text);
        padding: 2px 10px;
        border-radius: 2px;
        font-weight: 600;
        font-size: 0.74rem;
        letter-spacing: 0.04em;
        font-family: 'Fira Code', monospace !important;
    }

    /* Блок формул */
    .formula-box {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-left: 3px solid var(--accent-navy);
        border-radius: 3px;
        padding: 13px 17px;
        font-family: 'Fira Code', monospace !important;
        font-size: 0.82rem;
        margin-bottom: 13px;
        line-height: 1.9;
        color: var(--text-main);
    }

    /* Заголовки секций */
    .section-header {
        font-family: 'Fira Code', monospace !important;
        font-size: 0.72rem;
        font-weight: 600;
        color: var(--accent-navy);
        letter-spacing: 0.12em;
        text-transform: uppercase;
        border-bottom: 1px solid var(--border);
        padding-bottom: 5px;
        margin: 22px 0 13px 0;
    }

    /* Кнопки */
    [data-testid="stButton"] button {
        font-family: 'Fira Code', monospace !important;
        font-weight: 500;
        letter-spacing: 0.03em;
        font-size: 0.8rem;
        border-radius: 3px;
    }
    [data-testid="stButton"] button[kind="primary"] {
        background-color: var(--accent-navy) !important;
        border-color: var(--accent-navy) !important;
        color: #faf6ee !important;
    }
    [data-testid="stButton"] button[kind="primary"]:hover {
        background-color: var(--accent-mid) !important;
        border-color: var(--accent-mid) !important;
    }
    [data-testid="stButton"] button:not([kind="primary"]) {
        background-color: transparent !important;
        border: 1px solid var(--border) !important;
        color: var(--text-muted) !important;
    }
    [data-testid="stButton"] button:not([kind="primary"]):hover {
        border-color: var(--accent-warm) !important;
        color: var(--accent-navy) !important;
    }

    /* Поля ввода и слайдеры */
    [data-testid="stNumberInput"] input,
    [data-testid="stTextInput"] input {
        background-color: var(--bg-card) !important;
        border-color: var(--border) !important;
        font-family: 'Fira Code', monospace !important;
    }

    /* Метрики */
    [data-testid="stMetric"] label {
        font-family: 'Fira Code', monospace !important;
        font-size: 0.75rem !important;
        color: var(--text-muted) !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Fira Code', monospace !important;
        color: var(--accent-navy) !important;
    }

    /* Таблицы dataframe */
    [data-testid="stDataFrame"] {
        font-family: 'Fira Code', monospace !important;
        font-size: 0.82rem !important;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Инициализация состояния сессии
# ─────────────────────────────────────────────
if "projects"     not in st.session_state: st.session_state.projects     = []
if "calculated"   not in st.session_state: st.session_state.calculated   = False
if "mutex_groups" not in st.session_state: st.session_state.mutex_groups = [] #группы взаимоисключающих проектов

# Палитра цветов для графиков
COLORS = ["#1e3a5f", "#c8773a", "#4a6fa5", "#8b4f2a", "#6a8fb5", "#a05a20", "#2a5a8a", "#d4954a"]


# ═════════════════════════════════════════════
# РАСЧЁТНЫЕ ФУНКЦИИ
# ═════════════════════════════════════════════
#сделать таблицу чтобы она выводилась
def build_cf_table(p: dict) -> pd.DataFrame:
    """
    Строит детальную таблицу денежных потоков по годам.
    Выручка, переменные и постоянные издержки, прибыль, налог, СДП.
    """
    rows = [] #в этот список будут добавляться строки будущей таблицы
    inf = p["inflation"] / 100 #инфляция
    tax = p["tax"] / 100 #налог на прибыль
    for t in range(1, p["years"] + 1): #цикл по годам
        factor     = (1 + inf) ** t #дисконт
        revenue    = p["volume"] * p["price"] * factor #выручка в году t
        var_costs  = p["volume"] * p["var_cost"] * factor #переменные издержки
        fixed      = p["fixed_cost"] * factor #постоянные издержки
        amort = p["invest"]/p["years"] #амортизация лин способ
        taxable_profit = revenue - var_costs - fixed - amort #налогооблагаемая прибыль (было gross)
        tax_amount = taxable_profit * tax if taxable_profit > 0 else 0.0 #налог
        net_profit        = taxable_profit - tax_amount #было net, это чистая прибыль
        cash_flow = net_profit + amort #свободные денежные потоки
        discounted_cf = cash_flow/factor #дискотированный денежный поток
        rows.append({
            "Год":               t,
            "Выручка":           round(revenue, 2),
            "Перем. издержки":   round(var_costs, 2),
            "Пост. издержки":    round(fixed, 2),
            "Амортизация": round(amort, 2),
            "Прибыль до налога": round(taxable_profit, 2),
            "Налог":             round(tax_amount, 2),
            "Чистая прибыль":round(net_profit, 2),
            "Денежный поток (СДП)": round(cash_flow, 2), #СДП
            "Дисконтированный (ДДП)": round(discounted_cf, 2) #ДДП
        })
    return pd.DataFrame(rows)


def build_cash_flows(p: dict) -> list: #денежный поток по годам таблица
    df = build_cf_table(p) #внешний словарь р передаётся в функцию
    return df["Денежный поток (СДП)"].tolist() #извлекает данную колонку и преобразует в список (это СДП)


def calc_npv(cfs: list, invest: float, rate_pct: float) -> float: #функция расчёта NPV с аннотациями
    r   = rate_pct / 100
    npv = -invest #в 0 году отрицательный
    for t, cf in enumerate(cfs, start=1): #нужно чтобы начинал с 1 года
        npv += cf / (1 + r) ** t #сумма ДДП
    return round(npv, 2)


def calc_irr(cfs: list, invest: float): #функция расчёта IRR
    all_flows = [-invest] + cfs #список свободных денежных потоков

    def npv_at(r): #расчёт NPV при заданной ставке
        return sum(cf / (1 + r) ** t for t, cf in enumerate(all_flows))

    if npv_at(0.0001) < 0:
        return None
    lo, hi = 0.0001, 10.0
    for _ in range(2000): #метод дихотомии
        mid = (lo + hi) / 2
        val = npv_at(mid)
        if abs(val) < 1e-6:
            return round(mid * 100, 2)
        if val > 0:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2 * 100, 2)


def calc_pi(cfs: list, invest: float, rate_pct: float) -> float: #функция расчёта PI
    r  = rate_pct / 100
    pv = sum(cf / (1 + r) ** t for t, cf in enumerate(cfs, start=1))
    return round(pv / invest, 3)


def calc_dpp(cfs: list, invest: float, rate_pct: float): #функция расчёта DPP
    r          = rate_pct / 100
    cumulative = 0.0 #накопленная сумма дисконтированных потоков
    for t, cf in enumerate(cfs, start=1):
        prev       = cumulative #переменная хранящая прошлый год 
        cumulative += cf / (1 + r) ** t #добавляем дисконтированный поток
        if cumulative >= invest:  #накопили достаточно?
            fraction = (invest - prev) / (cf / (1 + r) ** t)
            return round(t - 1 + fraction, 2)
    return None # так и не окупилось


def calc_pp(cfs: list, invest: float): #функция расчёта PP
    """Простой (недисконтированный) срок окупаемости."""
    cumulative = 0.0
    for t, cf in enumerate(cfs, start=1):
        prev       = cumulative
        cumulative += cf  #просто складываем, не дисконтируем
        if cumulative >= invest:
            fraction = (invest - prev) / cf
            return round(t - 1 + fraction, 2)
    return None


def calc_bep(p: dict) -> float: #точка безубыточности в натуральном выражении
    margin = p["price"] - p["var_cost"] #маржа на 1 ед
    if margin <= 0: #если цена ниже или равна переменным затратам
        return float("inf") #бесконечность, т.к. безубыточность недостижима
    return round(p["fixed_cost"] / margin, 1) #сколько единиц нужно продать


def bep_advice(p: dict, bep: float, npv: float) -> tuple: #рекоммендации
    volume = p["volume"]
    margin = p["price"] - p["var_cost"]

    if npv >= 0 and bep <= volume: #случай 1 всё отлично
        safety = (1 - bep / volume) * 100 # запас прочности в %
        return (
            f"Проект эффективен. Точка безубыточности ({_n(bep, 0)} ед.) "
            f"ниже планового выпуска ({_n(volume, 0)} ед.). "
            f"Запас прочности: {safety:.1f}%.",
            "good"
        )

    advices = []

    if bep == float("inf") or margin <= 0: #случай 2 цена ниже переменных затрат
        advices.append(
            f"Внимание. Цена ({p['price']:.2f} Р) ≤ переменных издержек на единицу "
            f"({p['var_cost']:.2f} Р). Проект заведомо убыточен. "
            f"Необходимо повысить цену или снизить переменные издержки."
        )
        return " ".join(advices), "warn"

    if bep > volume: #случай 3  низкий плановый выпуск
        req_volume = round(bep * 1.1)
        req_price  = round(p["var_cost"] + p["fixed_cost"] / volume, 2)
        max_var    = round(p["price"] - p["fixed_cost"] / volume, 2)
        max_fixed  = round(margin * volume, 2)
        advices.append(
            f"Точка безубыточности для объёма продукции (BEP) ({_n(bep, 0)} ед.) превышает плановый выпуск ({_n(volume, 0)} ед.). "
            f"Проект не достигает безубыточности. Варианты исправления:"
            f"<br>• Увеличить объём выпуска до ≥ {_n(req_volume, 0)} ед."
            f"<br>• Повысить цену до ≥ {req_price:.2f} Р/ед. (сейчас {p['price']:.2f} Р)"
            f"<br>• Снизить перем. издержки до ≤ {max_var:.2f} Р/ед. (сейчас {p['var_cost']:.2f} Р)"
            f"<br>• Снизить пост. издержки до ≤ {_n(max_fixed, 0)} Р/год (сейчас {_n(p['fixed_cost'], 0)} Р)"
        )

    if npv < 0 and bep <= volume: #случай 4 NPV отрицательный
        advices.append(
            f"Внимание. Точка безубыточности для объёма продукции (BEP) достигается, но NPV = {_n(npv, 0)} Р (отрицательный). "
            f"Проект прибылен операционно, однако с учётом дисконтирования "
            f"не окупает начальные инвестиции. Рекомендации: снизить инвестиции, "
            f"увеличить горизонт проекта или повысить цену."
        )

    return "".join(advices), "warn"


def compute_all(projects: list) -> list: #для анализа всех проектов
    results = []
    for p in projects: #словарь с параметрами проекта
        cfs   = build_cash_flows(p)
        npv   = calc_npv(cfs, p["invest"], p["rate"])
        irr   = calc_irr(cfs, p["invest"])
        pi    = calc_pi(cfs, p["invest"], p["rate"])
        dpp   = calc_dpp(cfs, p["invest"], p["rate"])
        pp    = calc_pp(cfs, p["invest"])
        bep   = calc_bep(p)
        adv, adv_type = bep_advice(p, bep, npv)
        df_cf = build_cf_table(p)
        results.append(dict(
            name=p["name"], npv=npv, irr=irr, pi=pi,
            dpp=dpp, pp=pp, bep=bep,
            cfs=cfs, df_cf=df_cf,
            invest=p["invest"], years=p["years"],
            advice=adv, advice_type=adv_type, params=p,
        ))
    return results # список словарей с результатами всех проектов


# ═════════════════════════════════════════════
# ТОЧКА ВХОДА — ЗАГОЛОВОК И ВКЛАДКИ
# ═════════════════════════════════════════════
st.title("Анализ инвестиционных проектов")
st.caption("Экономическая оценка · моделирование денежных потоков · показатели эффективности")

tab1, tab2, tab3, tab4 = st.tabs([
    "Ввод проектов",
    "Показатели эффективности",
    "Оптимальный портфель",
    "Риск и чувствительность",
])


# ═════════════════════════════════════════════
# ВКЛАДКА 1 — ВВОД ПРОЕКТОВ
# ═════════════════════════════════════════════
with tab1:
    st.subheader("Добавление инвестиционных проектов")
    st.markdown("Введите параметры каждого проекта. Можно добавить до **20 проектов** для сравнения.")

    with st.expander("+ Добавить новый проект", expanded=len(st.session_state.projects) == 0):
        col_l, col_r = st.columns(2)

        with col_l:
            st.markdown("**Основные параметры**")
            name       = st.text_input("Название проекта", placeholder="Проект А")
            invest     = st.number_input("Начальные инвестиции (Р)", min_value=0.0,
                                          value=1_000_000.0, step=50_000.0, format="%.2f")
            years      = st.slider("Срок проекта (лет)", 1, 15, 5)
            volume     = st.number_input("Объём выпуска (ед./год)", min_value=1.0,
                                          value=1000.0, step=100.0)
            price      = st.number_input("Цена единицы (Р)", min_value=0.0,
                                          value=1500.0, step=50.0)

        with col_r:
            st.markdown("**Издержки и ставки**")
            var_cost   = st.number_input("Переменные издержки на ед. (Р)", min_value=0.0,
                                          value=800.0, step=50.0)
            fixed_cost = st.number_input("Постоянные издержки/год (Р)", min_value=0.0,
                                          value=200_000.0, step=10_000.0, format="%.2f")
            tax        = st.number_input("Ставка налога на прибыль (%)", min_value=0.0,
                                          max_value=100.0, value=20.0, step=1.0)
            inflation  = st.number_input("Инфляция (%/год)", min_value=0.0,
                                          max_value=50.0, value=5.0, step=0.5)
            rate       = st.number_input("Барьерная/банковская ставка (%)", min_value=0.0,
                                          max_value=100.0, value=12.0, step=0.5)

        if st.button("Добавить проект", type="primary",
                      disabled=len(st.session_state.projects) >= 20):
            if not name.strip():
                st.error("Введите название проекта.")
            else:
                st.session_state.projects.append(dict(
                    name=name.strip(), invest=invest, years=years,
                    volume=volume, price=price, var_cost=var_cost,
                    fixed_cost=fixed_cost, tax=tax, inflation=inflation, rate=rate
                ))
                st.session_state.calculated = False
                st.success(f"Проект «{name}» добавлен!")
                st.rerun()

    if st.session_state.projects:
        st.markdown(f"### Добавлено проектов: {len(st.session_state.projects)}")
        for idx, p in enumerate(st.session_state.projects):
            st.markdown(f"""
            <div class="project-card">
                <strong>#{idx+1} · {p['name']}</strong>
            </div>""", unsafe_allow_html=True)

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Инвестиции",  f"{_n(p['invest'], 0)} Р")
            c2.metric("Срок",         f"{p['years']} лет")
            c3.metric("Выпуск/год",   f"{_n(p['volume'], 0)} ед.")
            c4.metric("Цена",         f"{_n(p['price'], 0)} Р")
            c5.metric("Ставка",       f"{p['rate']}%")

            ci, ce, cd = st.columns([4, 1, 1])
            ci.caption(
                f"Перем. изд.: {p['var_cost']} Р/ед. · "
                f"Пост. изд.: {_n(p['fixed_cost'], 0)} Р/год · "
                f"Налог: {p['tax']}% · Инфляция: {p['inflation']}%"
            )
            if ce.button("Редактировать", key=f"edit_btn_{idx}", help="Редактировать проект"):
                st.session_state[f"editing_{idx}"] = not st.session_state.get(f"editing_{idx}", False)
                st.rerun()
            if cd.button("Удалить", key=f"del_{idx}", help="Удалить проект"):
                st.session_state.projects.pop(idx)
                # Сбрасываем флаг редактирования если был открыт
                st.session_state.pop(f"editing_{idx}", None)
                st.session_state.calculated = False
                st.rerun()

            # — Форма редактирования проекта —
            if st.session_state.get(f"editing_{idx}", False):
                with st.container():
                    st.markdown(f"**Редактирование: {p['name']}**")
                    ecol_l, ecol_r = st.columns(2)
                    with ecol_l:
                        e_name       = st.text_input("Название",          value=p["name"],       key=f"e_name_{idx}")
                        e_invest     = st.number_input("Начальные инвестиции (Р)", value=p["invest"],   min_value=0.0, step=50_000.0, format="%.2f", key=f"e_invest_{idx}")
                        e_years      = st.slider("Срок проекта (лет)",    value=p["years"],      min_value=1, max_value=15, key=f"e_years_{idx}")
                        e_volume     = st.number_input("Объём выпуска (ед./год)", value=p["volume"],   min_value=1.0, step=100.0, key=f"e_volume_{idx}")
                        e_price      = st.number_input("Цена единицы (Р)", value=p["price"],     min_value=0.0, step=50.0, key=f"e_price_{idx}")
                    with ecol_r:
                        e_var_cost   = st.number_input("Перем. издержки на ед. (Р)", value=p["var_cost"],  min_value=0.0, step=50.0, key=f"e_var_{idx}")
                        e_fixed_cost = st.number_input("Пост. издержки/год (Р)", value=p["fixed_cost"], min_value=0.0, step=10_000.0, format="%.2f", key=f"e_fixed_{idx}")
                        e_tax        = st.number_input("Налог на прибыль (%)", value=p["tax"],      min_value=0.0, max_value=100.0, step=1.0, key=f"e_tax_{idx}")
                        e_inflation  = st.number_input("Инфляция (%/год)",  value=p["inflation"], min_value=0.0, max_value=50.0, step=0.5, key=f"e_inf_{idx}")
                        e_rate       = st.number_input("Барьерная ставка (%)", value=p["rate"],     min_value=0.0, max_value=100.0, step=0.5, key=f"e_rate_{idx}")
                    if st.button("Сохранить изменения", key=f"save_{idx}", type="primary"):
                        st.session_state.projects[idx] = dict(
                            name=e_name.strip(), invest=e_invest, years=e_years,
                            volume=e_volume, price=e_price, var_cost=e_var_cost,
                            fixed_cost=e_fixed_cost, tax=e_tax, inflation=e_inflation, rate=e_rate
                        )
                        st.session_state[f"editing_{idx}"] = False
                        st.session_state.calculated = False
                        st.success(f"Проект «{e_name}» обновлён!")
                        st.rerun()
                    st.divider()

        st.divider()
        if st.button("Рассчитать все проекты", type="primary"):
            st.session_state.calculated = True
            st.rerun()
    else:
        st.info("Добавьте хотя бы один проект для начала анализа.")


# ═════════════════════════════════════════════
# ВКЛАДКА 2 — ПОКАЗАТЕЛИ ЭФФЕКТИВНОСТИ
# ═════════════════════════════════════════════
with tab2:
    if not st.session_state.calculated or not st.session_state.projects:
        st.info("Сначала добавьте проекты и нажмите «Рассчитать» на вкладке ввода.")
        st.stop()

    results = compute_all(st.session_state.projects)

    # ── 2.1 Сводная таблица ───────────────────
    st.markdown('<div class="section-header">Сводная таблица показателей эффективности</div>',
                unsafe_allow_html=True)

    rows = []
    for r in results:
        irr_s = f"{r['irr']:.2f}%"  if r["irr"] is not None else "н/д"
        dpp_s = f"{r['dpp']:.2f} л" if r["dpp"] is not None else "не окупается"
        pp_s  = f"{r['pp']:.2f} л"  if r["pp"]  is not None else "не окупается"
        bep_s = f"{_n(r['bep'], 0)}"  if r["bep"] != float("inf") else "∞"
        eff   = (r["npv"] >= 0) and (r["pi"] >= 1)
        rows.append({
            "Проект":    r["name"],
            "NPV, Р": r["npv"],
            "IRR":       irr_s,
            "PI":        r["pi"],
            "PP, лет":   pp_s,
            "DPP, лет":  dpp_s,
            "BEP, ед.":  bep_s,
            "Вывод":     "Эффективен" if eff else "Не эффективен",
        })

    df_sum = pd.DataFrame(rows)

    def style_npv(v):
        return "color:#1e3a5f;font-weight:600" if v >= 0 else "color:#a03020;font-weight:600"

    def style_pi(v):
        return "color:#1e3a5f;font-weight:600" if v >= 1 else "color:#a03020;font-weight:600"

    try:
        # pandas >= 2.1
        styled = (
            df_sum.style
            .map(style_npv, subset=["NPV, Р"])
            .map(style_pi,  subset=["PI"])
            .format({"NPV, Р": lambda v: _n(v, 0), "PI": "{:.3f}"})
        )
    except AttributeError:
        # pandas < 2.1
        styled = (
            df_sum.style
            .applymap(style_npv, subset=["NPV, Р"])
            .applymap(style_pi,  subset=["PI"])
            .format({"NPV, Р": lambda v: _n(v, 0), "PI": "{:.3f}"})
        )

    st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── 2.2 Сравнительный график NPV ──────────
    st.markdown('<div class="section-header">Сравнение NPV по проектам</div>',
                unsafe_allow_html=True)

    fig_npv = go.Figure(go.Bar(
        x=[r["name"] for r in results],
        y=[r["npv"]  for r in results],
        marker_color=["#1e3a5f" if r["npv"] >= 0 else "#a03020" for r in results],
        text=[f"{_n(r['npv'], 0)} Р" for r in results],
        textposition="outside",
    ))
    fig_npv.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
    fig_npv.update_layout(
        height=340, margin=dict(t=30, b=10),
        plot_bgcolor="white",
        yaxis=dict(title="NPV, Р", gridcolor="#eee"),
        xaxis=dict(title="Проект"),
    )
    st.plotly_chart(fig_npv, use_container_width=True, key="fig_npv_main")

    # ── 2.3 Детальный разбор по каждому проекту ─
    st.markdown('<div class="section-header">Детальный разбор по каждому проекту</div>',
                unsafe_allow_html=True)

    for i, r in enumerate(results):
        p = r["params"]
        with st.expander(f"{r['name']}", expanded=(i == 0)):

            # — Формулы с подстановкой чисел —
            st.markdown("**Применяемые формулы и расчёт**")
            r_dec   = p["rate"] / 100
            irr_str = f"{r['irr']:.2f}%" if r["irr"] is not None else "не определена"

            npv_terms = " + ".join(
                f"{_n(cf, 0)}/(1+{r_dec:.2f})^{t}"
                for t, cf in enumerate(r["cfs"], start=1)
            )

            st.markdown(f"""
<div class="formula-box">
<b>NPV</b> = −I₀ + Σ СДП_t / (1+r)^t<br>
NPV = −{_n(p['invest'], 0)} + {npv_terms}<br>
<b>NPV = {_n(r['npv'], 0)} Р</b><br><br>
<b>IRR</b> — ставка при которой NPV = 0 &nbsp;→&nbsp; <b>IRR = {irr_str}</b><br><br>
<b>PI</b> = PV(СДП) / I₀ = (NPV + I₀) / I₀
&nbsp;= ({_n(r['npv'], 0)} + {_n(p['invest'], 0)}) / {_n(p['invest'], 0)}
&nbsp;= <b>{r['pi']:.3f}</b><br><br>
<b>BEP</b> = Пост.изд. / (Цена − Перем.изд./ед.)
&nbsp;= {_n(p['fixed_cost'], 0)} / ({p['price']:.2f} − {p['var_cost']:.2f})
&nbsp;= <b>{_n(r['bep'], 1)} ед.</b>
</div>""", unsafe_allow_html=True)

            # — Вывод по критериям —
            st.markdown("**Оценка по критериям**")
            rate     = p["rate"]
            irr_val  = r["irr"] if r["irr"] is not None else 0

            criteria = [
                ("NPV > 0",
                 f"NPV = {_n(r['npv'], 0)} Р",
                 r["npv"] >= 0),
                (f"IRR > r ({rate}%)",
                 f"IRR = {irr_str}",
                 r["irr"] is not None and irr_val > rate),
                ("PI > 1",
                 f"PI = {r['pi']:.3f}",
                 r["pi"] >= 1),
                (f"DPP ≤ срока проекта ({p['years']} лет)",
                 f"DPP = {r['dpp']} лет" if r["dpp"] else "не окупается",
                 r["dpp"] is not None and r["dpp"] <= p["years"]),
                (f"BEP ≤ выпуска ({_n(p['volume'], 0)} ед.)",
                 f"BEP = {_n(r['bep'], 0)} ед." if r["bep"] != float("inf") else "BEP = ∞",
                 r["bep"] != float("inf") and r["bep"] <= p["volume"]),
            ]

            html_crit = ""
            for criterion, value, ok in criteria:
                badge = '<span class="badge-ok">✓ Выполняется</span>' if ok \
                        else '<span class="badge-bad">✗ Не выполняется</span>'
                html_crit += (
                    f'<div class="criterion-row">{badge}'
                    f'&nbsp;<b>{criterion}</b> — {value}</div>'
                )
            st.markdown(html_crit, unsafe_allow_html=True)

            # — Таблица СДП по годам —
            st.markdown("**Таблица свободных денежных потоков по годам**") #свободные СДП
            df_cf_disp = r["df_cf"].copy()
            for col in df_cf_disp.columns:
                if col != "Год":
                    df_cf_disp[col] = df_cf_disp[col].apply(lambda x: f"{_n(x, 2)}")
            st.dataframe(df_cf_disp, use_container_width=True, hide_index=True)

            # — График СДП по годам —
            cfs_vals = r["cfs"]
            fig_cf = go.Figure(go.Bar(
                x=[f"Год {t}" for t in range(1, r["years"] + 1)],
                y=cfs_vals,
                marker_color=[
                    COLORS[i % len(COLORS)] if v >= 0 else "#c4907a"
                    for v in cfs_vals
                ],
                text=[f"{_n(v, 0)}" for v in cfs_vals],
                textposition="outside",
            ))
            fig_cf.update_layout(
                title="Свободные денежные потоки (СДП) по годам", #Чистая прибыль (СДП) по годам
                height=280, margin=dict(t=40, b=10),
                plot_bgcolor="white",
                yaxis=dict(title="СДП, Р", gridcolor="#eee"),
                showlegend=False,
            )
            st.plotly_chart(fig_cf, use_container_width=True, key=f"fig_cf_{i}")

            # — График накопленного дисконтированного ДДП —
            rate_dec = p["rate"] / 100
            cum = [-p["invest"]]
            for t, cf in enumerate(r["cfs"], start=1):
                cum.append(cum[-1] + cf / (1 + rate_dec) ** t)

            x_ax    = [f"Год {t}" for t in range(r["years"] + 1)]
            x_ax[0] = "Год 0"

            fig_cum = go.Figure()
            fig_cum.add_trace(go.Scatter(
                x=x_ax, y=cum,
                mode="lines+markers",
                line=dict(color=COLORS[i % len(COLORS)], width=2.5),
                marker=dict(size=7),
                fill="tozeroy",
                fillcolor="rgba(41,98,255,0.07)",
            ))
            fig_cum.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1.5)
            fig_cum.update_layout(
                title="Накопленный дисконтированный денежный поток (ДДП, окупаемость)",
                height=300, margin=dict(t=40, b=10),
                plot_bgcolor="white",
                yaxis=dict(title="Руб.", gridcolor="#eee"),
                showlegend=False,
            )
            st.plotly_chart(fig_cum, use_container_width=True, key=f"fig_cum_{i}")

            # — График BEP —
            if r["bep"] != float("inf"):
                q_max      = max(p["volume"] * 1.5, r["bep"] * 1.5, 1)
                q_range    = [q_max * j / 100 for j in range(101)]
                revenue    = [q * p["price"] for q in q_range]
                total_cost = [p["fixed_cost"] + q * p["var_cost"] for q in q_range]

                fig_bep = go.Figure()
                fig_bep.add_trace(go.Scatter(
                    x=q_range, y=revenue, name="Выручка",
                    line=dict(color="#1e3a5f", width=2)
                ))
                fig_bep.add_trace(go.Scatter(
                    x=q_range, y=total_cost, name="Полные издержки",
                    line=dict(color="#a03020", width=2)
                ))
                fig_bep.add_vline(
                    x=r["bep"], line_dash="dot", line_color="#c8773a",
                    annotation_text=f"BEP={_n(r['bep'], 0)} ед.",
                    annotation_position="top right"
                )
                fig_bep.add_vline(
                    x=p["volume"], line_dash="dot", line_color="#1e3a5f",
                    annotation_text=f"Выпуск={_n(p['volume'], 0)} ед.",
                    annotation_position="top left"
                )
                fig_bep.update_layout(
                    title="График безубыточности",
                    height=300, margin=dict(t=40, b=10),
                    plot_bgcolor="white",
                    yaxis=dict(title="Руб.", gridcolor="#eee"),
                    xaxis=dict(title="Объём, ед."),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                )
                st.plotly_chart(fig_bep, use_container_width=True, key=f"fig_bep_{i}")

            # — Совет на основе BEP —
            css = "advice-box good" if r["advice_type"] == "good" else "advice-box"
            st.markdown(
                f'<div class="{css}">{r["advice"]}</div>',
                unsafe_allow_html=True
            )


# ═════════════════════════════════════════════
# ВКЛАДКА 3 — ОПТИМАЛЬНЫЙ ПОРТФЕЛЬ (многокритериальная ЛП)
# ═════════════════════════════════════════════
with tab3:
    if not st.session_state.calculated or not st.session_state.projects:
        st.info("Сначала добавьте проекты и нажмите «Рассчитать» на вкладке ввода.")
        st.stop()

    if not PULP_AVAILABLE:
        st.error(
            "Библиотека **PuLP** не установлена. "
            "Выполните в терминале:\n\n```\npip install pulp\n```\n\nи перезапустите приложение."
        )
        st.stop()

    results_lp = compute_all(st.session_state.projects)

    st.subheader("Формирование оптимального инвестиционного портфеля")
    st.markdown(
        "Используется **многокритериальная оптимизация методом взвешенной суммы**: "
        "два критерия — NPV и PI — объединяются в единую целевую функцию через нормализацию "
        "и веса. Изменяя веса, можно исследовать, как меняется состав портфеля при смещении "
        "приоритета с абсолютной доходности на относительную эффективность инвестиций."
    )

    # ── Постановка задачи ─────────────────────
    st.markdown('<div class="section-header">Постановка задачи</div>',
                unsafe_allow_html=True)

    st.markdown(r"""
**Метод взвешенной суммы** сводит многокритериальную задачу к одному критерию:

$$\max Z = \alpha \cdot \sum_{i=1}^{n} \widetilde{NPV}_i \cdot x_i \;+\; \beta \cdot \sum_{i=1}^{n} \widetilde{PI}_i \cdot x_i$$

где $\widetilde{NPV}_i = \dfrac{NPV_i}{NPV_{\max}}$ и $\widetilde{PI}_i = \dfrac{PI_i}{PI_{\max}}$ — нормализованные значения (от 0 до 1),
$\alpha$ и $\beta$ — веса критериев ($\alpha + \beta = 1$).

**Ограничения:**
- Бюджетное: $\sum I_i \cdot x_i \leq B$
- Бинарность: $x_i \in \{0, 1\}$
- Взаимоисключение (опционально): $x_s + \ldots + x_k = 1$
""")

    # ── Параметры задачи ──────────────────────
    st.markdown('<div class="section-header">Параметры оптимизации</div>',
                unsafe_allow_html=True)

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        total_budget = st.number_input(
            "Общий бюджет (Р)",
            min_value=0.0,
            value=float(sum(p["invest"] for p in st.session_state.projects) * 0.7),
            step=100_000.0,
            format="%.2f",
            help="Максимальная сумма, которую можно вложить во все проекты"
        )
    with col_b2:
        only_positive = st.checkbox(
            "Включать только проекты с NPV > 0",
            value=True,
            help="Если отмечено — убыточные проекты не рассматриваются"
        )

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        min_projects = st.number_input(
            "Минимальное число проектов в портфеле",
            min_value=0,
            max_value=len(st.session_state.projects),
            value=0,
            step=1,
        )
    with col_c2:
        max_projects = st.number_input(
            "Максимальное число проектов в портфеле",
            min_value=1,
            max_value=len(st.session_state.projects),
            value=len(st.session_state.projects),
            step=1,
        )

    # ── Веса критериев ────────────────────────
    st.markdown('<div class="section-header">Веса критериев (α + β = 1)</div>',
                unsafe_allow_html=True)
    st.markdown(
        "**α** — вес критерия NPV (абсолютная доходность портфеля).  \n"
        "**β** — вес критерия PI (относительная эффективность на рубль вложений).  \n"
        "При α = 1 задача сводится к классической максимизации NPV; "
        "при β = 1 — к максимизации средневзвешенного PI."
    )
    alpha = st.slider(
        "α — вес NPV",
        min_value=0.0, max_value=1.0, value=0.6, step=0.05,
        help="β вычисляется автоматически как 1 − α"
    )
    beta = round(1.0 - alpha, 10)
    st.caption(f"β (вес PI) = {beta:.2f}")

    # ── Взаимоисключающие проекты ─────────────
    st.markdown('<div class="section-header">Взаимоисключающие проекты (опционально)</div>',
                unsafe_allow_html=True)
    st.markdown(
        "Для каждой группы будет добавлено ограничение **x_s + … + x_k = 1** — "
        "из группы реализуется ровно один проект."
    )

    project_name_list = [p["name"] for p in st.session_state.projects]

    if st.session_state.mutex_groups:
        st.markdown("**Добавленные группы взаимоисключения:**")
        for g_idx, group in enumerate(st.session_state.mutex_groups):
            col_g, col_del = st.columns([6, 1])
            col_g.markdown(
                f"**Группа {g_idx + 1}:** "
                + " + ".join(f"`{name}`" for name in group)
                + " = 1"
            )
            if col_del.button("Удалить", key=f"del_mutex_{g_idx}"):
                st.session_state.mutex_groups.pop(g_idx)
                st.rerun()

    with st.expander("Добавить группу взаимоисключающих проектов", expanded=False):
        st.caption("Выберите не менее 2 проектов. Из выбранных в портфель войдёт ровно один.")
        mutex_selected = st.multiselect(
            "Проекты в группе",
            options=project_name_list,
            key="mutex_multiselect",
            placeholder="Выберите проекты..."
        )
        if st.button("Добавить группу", key="add_mutex_group"):
            if len(mutex_selected) < 2:
                st.error("Выберите не менее 2 проектов.")
            else:
                existing_names = {name for g in st.session_state.mutex_groups for name in g}
                overlap = set(mutex_selected) & existing_names
                if overlap:
                    st.error(f"Проекты {', '.join(overlap)} уже в другой группе.")
                else:
                    st.session_state.mutex_groups.append(list(mutex_selected))
                    st.success("Группа добавлена: " + " + ".join(f"x({n})" for n in mutex_selected) + " = 1")
                    st.rerun()

    run_lp = st.button("Решить задачу оптимизации", type="primary")

    if run_lp:

        # ── Фильтрация кандидатов ─────────────
        candidates = [r for r in results_lp if (not only_positive or r["npv"] > 0)]

        if not candidates:
            st.warning("Нет проектов, удовлетворяющих условиям.")
            st.stop()

        # ── Нормализация NPV и PI ─────────────
        # Делим каждое значение на максимум среди кандидатов → диапазон [0, 1]
        max_npv = max(r["npv"] for r in candidates)
        max_pi  = max(r["pi"]  for r in candidates)
        # Защита от деления на 0
        max_npv = max_npv if max_npv != 0 else 1.0
        max_pi  = max_pi  if max_pi  != 0 else 1.0

        norm_npv = {r["name"]: r["npv"] / max_npv for r in candidates}
        norm_pi  = {r["name"]: r["pi"]  / max_pi  for r in candidates}

        # ── Взвешенный скор для каждого проекта ─
        score = {
            r["name"]: alpha * norm_npv[r["name"]] + beta * norm_pi[r["name"]]
            for r in candidates
        }

        # ── Решение задачи ILP через PuLP ─────
        prob = pulp.LpProblem("MultiCriteriaPortfolio", pulp.LpMaximize)

        x = {
            r["name"]: pulp.LpVariable(f"x_{i}", cat="Binary")
            for i, r in enumerate(candidates)
        }

        # Целевая функция: max Σ score_i * x_i
        prob += pulp.lpSum(score[r["name"]] * x[r["name"]] for r in candidates), "WeightedScore"

        # Бюджет
        prob += (
            pulp.lpSum(r["invest"] * x[r["name"]] for r in candidates) <= total_budget,
            "Budget"
        )
        # Мин. кол-во проектов
        if min_projects > 0:
            prob += (
                pulp.lpSum(x[r["name"]] for r in candidates) >= min_projects,
                "MinProjects"
            )
        # Макс. кол-во проектов
        prob += (
            pulp.lpSum(x[r["name"]] for r in candidates) <= max_projects,
            "MaxProjects"
        )

        # Взаимоисключения
        candidate_names   = {r["name"] for r in candidates}
        valid_mutex_groups = []
        for g_idx, group in enumerate(st.session_state.mutex_groups):
            group_in_candidates = [name for name in group if name in candidate_names]
            if len(group_in_candidates) >= 2:
                prob += (
                    pulp.lpSum(x[name] for name in group_in_candidates) == 1,
                    f"MutualExclusion_{g_idx + 1}"
                )
                valid_mutex_groups.append(group_in_candidates)
            elif len(group_in_candidates) == 1:
                st.warning(
                    f"Группа {g_idx + 1}: только «{group_in_candidates[0]}» является кандидатом — "
                    f"ограничение взаимоисключения не применяется."
                )

        solver     = pulp.PULP_CBC_CMD(msg=False)
        status     = prob.solve(solver)
        status_str = pulp.LpStatus[prob.status]

        # ── Результаты ────────────────────────
        st.markdown('<div class="section-header">Результаты оптимизации</div>',
                    unsafe_allow_html=True)

        if status_str == "Optimal":

            selected   = [r for r in candidates if pulp.value(x[r["name"]]) == 1]
            rejected   = [r for r in results_lp  if r not in selected]
            total_npv  = sum(r["npv"]    for r in selected)
            total_inv  = sum(r["invest"] for r in selected)
            total_pi   = sum(r["pi"]     for r in selected) / len(selected) if selected else 0
            budget_use = total_inv / total_budget * 100 if total_budget > 0 else 0
            z_val      = sum(score[r["name"]] for r in selected)

            # Метрики портфеля
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Проектов в портфеле", len(selected))
            m2.metric("Суммарный NPV",        f"{_n(total_npv, 0)} Р")
            m3.metric("Средний PI портфеля",  f"{total_pi:.3f}")
            m4.metric("Использовано бюджета", f"{_n(total_inv, 0)} Р")
            m5.metric("Загрузка бюджета",     f"{budget_use:.1f}%")

            st.divider()

            # ── Таблица скоров всех кандидатов ─
            st.markdown("#### Скоры кандидатов (взвешенная сумма)")
            score_rows = []
            for r in candidates:
                in_p = r in selected
                score_rows.append({
                    "Проект":           r["name"],
                    "NPV, Р":           _n(r["npv"], 0),
                    "PI":               f"{r['pi']:.3f}",
                    f"NPV норм. (×{alpha:.2f})": f"{norm_npv[r['name']]:.3f}",
                    f"PI норм. (×{beta:.2f})":   f"{norm_pi[r['name']]:.3f}",
                    "Скор Z":           f"{score[r['name']]:.4f}",
                    "В портфеле":       "✓" if in_p else "—",
                })
            st.dataframe(pd.DataFrame(score_rows), use_container_width=True, hide_index=True)

            st.divider()

            # Таблица выбранных проектов
            st.markdown("#### Проекты, включённые в портфель")
            if selected:
                rows_sel = []
                for r in selected:
                    irr_s = f"{r['irr']:.2f}%" if r["irr"] is not None else "н/д"
                    rows_sel.append({
                        "Проект":        r["name"],
                        "Инвестиции, Р": _n(r["invest"], 0),
                        "NPV, Р":        _n(r["npv"], 0),
                        "IRR":           irr_s,
                        "PI":            f"{r['pi']:.3f}",
                        "Скор Z":        f"{score[r['name']]:.4f}",
                        "Доля бюджета":  f"{r['invest']/total_budget*100:.1f}%",
                    })
                st.dataframe(pd.DataFrame(rows_sel), use_container_width=True, hide_index=True)
            else:
                st.info("Ни один проект не выбран при заданных ограничениях.")

            # Таблица отклонённых
            st.markdown("#### Проекты, не включённые в портфель")
            if rejected:
                rows_rej = []
                for r in rejected:
                    if r["npv"] <= 0 and only_positive:
                        reason = "NPV ≤ 0 (фильтр)"
                    elif total_inv + r["invest"] > total_budget:
                        reason = "Нехватка бюджета"
                    else:
                        reason = "Не улучшает целевую функцию"
                    rows_rej.append({
                        "Проект":        r["name"],
                        "Инвестиции, Р": _n(r["invest"], 0),
                        "NPV, Р":        _n(r["npv"], 0),
                        "PI":            f"{r['pi']:.3f}",
                        "Причина":       reason,
                    })
                st.dataframe(pd.DataFrame(rows_rej), use_container_width=True, hide_index=True)

            st.divider()

            # ── Визуализация ──────────────────
            st.markdown("#### Визуализация портфеля")

            col_g1, col_g2 = st.columns(2)

            with col_g1:
                # Скоры всех кандидатов
                names_c  = [r["name"] for r in candidates]
                scores_c = [score[r["name"]] for r in candidates]
                in_port  = [r in selected for r in candidates]

                fig_score = go.Figure(go.Bar(
                    x=names_c,
                    y=scores_c,
                    marker_color=["#1e3a5f" if inc else "#c8bfb0" for inc in in_port],
                    text=[f"{s:.3f}" for s in scores_c],
                    textposition="outside",
                ))
                fig_score.update_layout(
                    title=f"Скор Z проектов (α={alpha:.2f}, β={beta:.2f})",
                    height=340, margin=dict(t=50, b=10),
                    plot_bgcolor="white",
                    yaxis=dict(title="Скор Z", gridcolor="#eee"),
                    showlegend=False,
                )
                st.plotly_chart(fig_score, use_container_width=True, key="fig_score")

            with col_g2:
                if selected:
                    fig_pie = go.Figure(go.Pie(
                        labels=[r["name"] for r in selected],
                        values=[r["invest"] for r in selected],
                        hole=0.45,
                        marker_colors=COLORS[:len(selected)],
                        textinfo="label+percent",
                    ))
                    fig_pie.update_layout(
                        title="Доли инвестиций в портфеле",
                        height=340, margin=dict(t=40, b=10),
                    )
                    st.plotly_chart(fig_pie, use_container_width=True, key="fig_pie")

            # ── Бюджет ────────────────────────
            st.markdown("#### Использование бюджета")
            fig_budget = go.Figure()
            fig_budget.add_trace(go.Bar(
                name="Использовано", x=["Бюджет"], y=[total_inv],
                marker_color="#1e3a5f",
                text=f"{_n(total_inv, 0)} Р", textposition="inside",
            ))
            fig_budget.add_trace(go.Bar(
                name="Остаток", x=["Бюджет"],
                y=[max(total_budget - total_inv, 0)],
                marker_color="#d8d0bc",
                text=f"{_n(max(total_budget - total_inv, 0), 0)} Р", textposition="inside",
            ))
            fig_budget.update_layout(
                barmode="stack", height=200, margin=dict(t=20, b=10),
                plot_bgcolor="white",
                yaxis=dict(title="Р", gridcolor="#eee"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            st.plotly_chart(fig_budget, use_container_width=True, key="fig_budget")

            # ── Анализ чувствительности к весам ─
            st.markdown('<div class="section-header">Анализ чувствительности к весам α / β</div>',
                        unsafe_allow_html=True)
            st.markdown(
                "Показывает, как меняется **состав портфеля и суммарный NPV** при изменении "
                "веса α от 0 до 1 (с шагом 0,1). Позволяет увидеть, при каком соотношении "
                "весов меняется оптимальный набор проектов."
            )

            alpha_range = [round(a * 0.1, 1) for a in range(11)]  # 0.0, 0.1, ..., 1.0
            sens_rows   = []
            prev_names  = None

            for a in alpha_range:
                b = round(1.0 - a, 10)
                sc = {r["name"]: a * norm_npv[r["name"]] + b * norm_pi[r["name"]] for r in candidates}

                prob_s = pulp.LpProblem(f"P_{a}", pulp.LpMaximize)
                xs = {r["name"]: pulp.LpVariable(f"y_{i}", cat="Binary") for i, r in enumerate(candidates)}
                prob_s += pulp.lpSum(sc[r["name"]] * xs[r["name"]] for r in candidates)
                prob_s += pulp.lpSum(r["invest"] * xs[r["name"]] for r in candidates) <= total_budget
                if min_projects > 0:
                    prob_s += pulp.lpSum(xs[r["name"]] for r in candidates) >= min_projects
                prob_s += pulp.lpSum(xs[r["name"]] for r in candidates) <= max_projects
                for g_idx, gin in enumerate(valid_mutex_groups):
                    prob_s += pulp.lpSum(xs[name] for name in gin) == 1, f"ME_{g_idx}_{a}"
                prob_s.solve(pulp.PULP_CBC_CMD(msg=False))

                sel_s   = [r for r in candidates if pulp.value(xs[r["name"]]) == 1]
                npv_s   = sum(r["npv"] for r in sel_s)
                pi_s    = sum(r["pi"]  for r in sel_s) / len(sel_s) if sel_s else 0
                names_s = ", ".join(r["name"] for r in sel_s) if sel_s else "—"
                changed = "◀ изменился" if prev_names is not None and names_s != prev_names else ""
                prev_names = names_s

                sens_rows.append({
                    "α (NPV)": f"{a:.1f}",
                    "β (PI)":  f"{b:.1f}",
                    "Состав портфеля": names_s,
                    "Суммарный NPV, Р": _n(npv_s, 0),
                    "Средний PI":       f"{pi_s:.3f}",
                    "":                 changed,
                })

            st.dataframe(pd.DataFrame(sens_rows), use_container_width=True, hide_index=True)

            # ── Формальная запись ─────────────
            st.markdown('<div class="section-header">Формальная запись решённой задачи</div>',
                        unsafe_allow_html=True)

            lp_lines = [
                "**Целевая функция (взвешенная сумма):**",
                f"max Z = α·Σ(NPV_норм·x_i) + β·Σ(PI_норм·x_i)",
                f"     = {alpha:.2f}·Σ(NPV_норм·x_i) + {beta:.2f}·Σ(PI_норм·x_i)",
                "",
                "**Нормализация:**",
                f"NPV_max = {_n(max_npv, 0)} Р   |   PI_max = {max_pi:.3f}",
                "",
                "**Скоры кандидатов:**",
            ]
            for r in candidates:
                lp_lines.append(
                    f"  Z({r['name']}) = {alpha:.2f}×{norm_npv[r['name']]:.3f}"
                    f" + {beta:.2f}×{norm_pi[r['name']]:.3f} = {score[r['name']]:.4f}"
                )
            lp_lines += [
                "",
                "**Ограничения:**",
                " + ".join(f"{_n(r['invest'], 0)}·x_{i+1}" for i, r in enumerate(candidates))
                + f" ≤ {_n(total_budget, 0)}  (бюджет)",
            ]
            if min_projects > 0:
                lp_lines.append(f"Σx_i ≥ {min_projects}  (мин. проектов)")
            lp_lines.append(f"Σx_i ≤ {max_projects}  (макс. проектов)")
            for g_idx, gin in enumerate(valid_mutex_groups):
                lp_lines.append(" + ".join(f"x({n})" for n in gin) + f" = 1  (взаимоисключение {g_idx+1})")
            lp_lines.append("x_i ∈ {0, 1}")
            lp_lines += [
                "",
                "**Оптимальное решение:**",
            ]
            for i, r in enumerate(candidates):
                val = int(pulp.value(x[r["name"]]))
                lp_lines.append(f"  x_{i+1} ({r['name']}) = {val}")
            lp_lines += [
                "",
                f"**Z* = {z_val:.4f}**",
                f"**Суммарный NPV портфеля = {_n(total_npv, 0)} Р**",
                f"**Средний PI портфеля    = {total_pi:.3f}**",
            ]

            st.markdown(
                '<div class="formula-box">' + "<br>".join(lp_lines) + "</div>",
                unsafe_allow_html=True
            )

            # ── Итоговый вывод ────────────────
            advice_lp = (
                f"Оптимальный портфель (α={alpha:.2f}, β={beta:.2f}): "
                f"{', '.join(r['name'] for r in selected)} — "
                f"суммарный NPV = {_n(total_npv, 0)} Р, средний PI = {total_pi:.3f}, "
                f"загрузка бюджета {budget_use:.1f}%."
            ) if selected else (
                "При заданных ограничениях ни один проект не вошёл в портфель. "
                "Увеличьте бюджет или снимите ограничения."
            )
            css_lp = "advice-box good" if selected else "advice-box"
            st.markdown(f'<div class="{css_lp}">{advice_lp}</div>', unsafe_allow_html=True)

        else:
            st.error(
                f"Задача не имеет оптимального решения (статус: {status_str}). "
                f"Проверьте ограничения."
            )


# ═════════════════════════════════════════════
# ВКЛАДКА 4 — РИСК И ЧУВСТВИТЕЛЬНОСТЬ
# ═════════════════════════════════════════════
with tab4:
    if not st.session_state.calculated or not st.session_state.projects:
        st.info("Сначала добавьте проекты и нажмите «Рассчитать» на вкладке ввода.")
        st.stop()

    results_r = compute_all(st.session_state.projects)

    st.subheader("Анализ риска и чувствительности")
    st.markdown(
        "Исследуем насколько NPV проекта устойчив к изменению входных параметров. "
        "Если NPV резко меняется при небольшом отклонении — проект **высокорисковый**."
    )

    # ── Выбор проекта ─────────────────────────
    project_names = [r["name"] for r in results_r]
    sel_name = st.selectbox("Выберите проект для анализа", project_names)
    sel_r    = next(r for r in results_r if r["name"] == sel_name)
    sel_p    = sel_r["params"]

    st.divider()

    # ══════════════════════════════════════════
    # БЛОК 1 — АНАЛИЗ ЧУВСТВИТЕЛЬНОСТИ
    # ══════════════════════════════════════════
    st.markdown('<div class="section-header">1. Анализ чувствительности NPV</div>',
                unsafe_allow_html=True)
    st.markdown(
        "Каждый параметр отклоняется от базового значения в диапазоне **−40% … +40%**, "
        "остальные параметры фиксированы. График показывает реакцию NPV."
    )

    # Параметры для анализа чувствительности
    sens_params = {
        "Цена (price)":                    "price",
        "Объём выпуска (volume)":          "volume",
        "Переменные издержки (var_cost)":  "var_cost",
        "Постоянные издержки (fixed_cost)":"fixed_cost",
        "Начальные инвестиции (invest)":   "invest",
        "Ставка дисконтирования (rate)":   "rate",
        "Инфляция (inflation)":            "inflation",
    }

    deviations = list(range(-40, 41, 5))   # от -40% до +40% с шагом 5%

    # Считаем NPV для каждого параметра при каждом отклонении
    sens_data = {}   # {label: [npv при каждом отклонении]}
    for label, key in sens_params.items():
        npv_series = []
        for dev in deviations:
            p_mod = dict(sel_p)
            p_mod[key] = sel_p[key] * (1 + dev / 100)
            # Ставка и инфляция не могут быть отрицательными
            if key in ("rate", "inflation", "tax"):
                p_mod[key] = max(p_mod[key], 0.01)
            cfs_mod = build_cash_flows(p_mod)
            npv_series.append(calc_npv(cfs_mod, p_mod["invest"], p_mod["rate"]))
        sens_data[label] = npv_series

    # ── «Паутинный» график чувствительности ──
    fig_sens = go.Figure()
    palette  = px.colors.qualitative.Bold

    for idx, (label, npv_series) in enumerate(sens_data.items()):
        fig_sens.add_trace(go.Scatter(
            x=deviations,
            y=npv_series,
            mode="lines",
            name=label,
            line=dict(color=palette[idx % len(palette)], width=2),
        ))

    fig_sens.add_hline(y=0,   line_dash="dash", line_color="black",  line_width=1.2,
                       annotation_text="NPV=0", annotation_position="right")
    fig_sens.add_vline(x=0,   line_dash="dot",  line_color="#999",   line_width=1)
    fig_sens.add_hline(y=sel_r["npv"], line_dash="dot", line_color="#c8773a", line_width=1,
                       annotation_text=f"Базовый NPV={_n(sel_r['npv'], 0)}",
                       annotation_position="right")

    fig_sens.update_layout(
        title=f"Чувствительность NPV к параметрам — {sel_name}",
        height=440,
        margin=dict(t=50, b=20),
        plot_bgcolor="white",
        xaxis=dict(title="Отклонение параметра, %", gridcolor="#eee", zeroline=False),
        yaxis=dict(title="NPV, Р", gridcolor="#eee"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    st.plotly_chart(fig_sens, use_container_width=True, key="fig_sens")

    # ── Таблица эластичности NPV ──────────────
    st.markdown("**Эластичность NPV по каждому параметру**")
    st.caption(
        "Эластичность = (ΔNPV / NPV_баз) / (ΔПараметра / Параметр_баз). "
        "Чем выше |эластичность|, тем сильнее NPV реагирует на изменение параметра."
    )

    base_npv = sel_r["npv"]
    elast_rows = []
    for label, key in sens_params.items():
        # Считаем при +10% отклонении
        p_plus = dict(sel_p)
        p_plus[key] = sel_p[key] * 1.10
        cfs_plus = build_cash_flows(p_plus)
        npv_plus = calc_npv(cfs_plus, p_plus["invest"], p_plus["rate"])

        if base_npv != 0:
            elasticity = ((npv_plus - base_npv) / base_npv) / 0.10
        else:
            elasticity = float("nan")

        # Критичный параметр: при каком отклонении NPV уходит в 0?
        critical = None
        for dev in range(1, 201):
            p_test = dict(sel_p)
            # Проверяем оба направления
            for sign in (-1, 1):
                p_test[key] = sel_p[key] * (1 + sign * dev / 100)
                if key in ("rate", "inflation", "tax"):
                    p_test[key] = max(p_test[key], 0.01)
                cfs_t = build_cash_flows(p_test)
                npv_t = calc_npv(cfs_t, p_test["invest"], p_test["rate"])
                if (base_npv > 0 and npv_t <= 0) or (base_npv < 0 and npv_t >= 0):
                    critical = sign * dev
                    break
            if critical is not None:
                break

        crit_str = f"{critical:+.0f}%" if critical is not None else "> ±200%"
        risk = (
            "Высокий"   if critical is not None and abs(critical) <= 15 else
            "Средний"   if critical is not None and abs(critical) <= 35 else
            "Низкий"
        )

        elast_rows.append({
            "Параметр":           label,
            "Базовое значение":   f"{_n(sel_p[key], 2)}",
            "Эластичность NPV":   f"{elasticity:.2f}" if elasticity == elasticity else "н/д",
            "Критич. отклонение": crit_str,
            "Риск":               risk,
        })

    df_elast = pd.DataFrame(elast_rows)
    st.dataframe(df_elast, use_container_width=True, hide_index=True)

    # ── Tornado chart ─────────────────────────
    st.markdown("**Диаграмма Торнадо** — влияние параметров на NPV при отклонении ±20%")

    tornado_rows = []
    for label, key in sens_params.items():
        p_lo = dict(sel_p); p_lo[key] = sel_p[key] * 0.80
        p_hi = dict(sel_p); p_hi[key] = sel_p[key] * 1.20
        for k in ("rate", "inflation", "tax"):
            p_lo[k] = max(p_lo.get(k, sel_p[k]), 0.01)
            p_hi[k] = max(p_hi.get(k, sel_p[k]), 0.01)
        npv_lo = calc_npv(build_cash_flows(p_lo), p_lo["invest"], p_lo["rate"])
        npv_hi = calc_npv(build_cash_flows(p_hi), p_hi["invest"], p_hi["rate"])
        swing  = abs(npv_hi - npv_lo)
        tornado_rows.append((label, npv_lo, npv_hi, swing))

    tornado_rows.sort(key=lambda x: x[3])   # сортируем по swing

    fig_torn = go.Figure()
    for label, npv_lo, npv_hi, _ in tornado_rows:
        lo_val = min(npv_lo, npv_hi) - base_npv
        hi_val = max(npv_lo, npv_hi) - base_npv
        fig_torn.add_trace(go.Bar(
            name=label,
            y=[label],
            x=[lo_val],
            base=base_npv,
            orientation="h",
            marker_color="#c4907a",
            showlegend=False,
            hovertemplate=f"{label}<br>−20%: {_n(npv_lo, 0)} Р<extra></extra>",
        ))
        fig_torn.add_trace(go.Bar(
            name=label,
            y=[label],
            x=[hi_val],
            base=base_npv,
            orientation="h",
            marker_color="#7a9fc0",
            showlegend=False,
            hovertemplate=f"{label}<br>+20%: {_n(npv_hi, 0)} Р<extra></extra>",
        ))

    fig_torn.add_vline(x=base_npv, line_dash="dash", line_color="#c8773a", line_width=2,
                       annotation_text=f"Базовый NPV", annotation_position="top")
    fig_torn.update_layout(
        barmode="overlay",
        title="Диаграмма Торнадо (красный = −20%, синий = +20%)",
        height=380, margin=dict(t=50, b=20, l=20),
        plot_bgcolor="white",
        xaxis=dict(title="NPV, Р", gridcolor="#eee"),
        yaxis=dict(title=""),
    )
    st.plotly_chart(fig_torn, use_container_width=True, key="fig_torn")

    st.divider()

    # ══════════════════════════════════════════
    # БЛОК 2 — СЦЕНАРНЫЙ АНАЛИЗ
    # ══════════════════════════════════════════
    st.markdown('<div class="section-header">2. Сценарный анализ</div>',
                unsafe_allow_html=True)
    st.markdown(
        "Три сценария развития событий: пессимистичный, базовый и оптимистичный. "
        "Параметры каждого сценария можно задать вручную."
    )

    scenario_defs = {
        "Пессимистичный": {"price": 0.85, "volume": 0.85, "var_cost": 1.15,
                               "fixed_cost": 1.10, "rate": 1.20, "invest": 1.10},
        "Базовый":        {"price": 1.00, "volume": 1.00, "var_cost": 1.00,
                               "fixed_cost": 1.00, "rate": 1.00, "invest": 1.00},
        "Оптимистичный":  {"price": 1.15, "volume": 1.15, "var_cost": 0.90,
                               "fixed_cost": 0.90, "rate": 0.85, "invest": 0.95},
    }

    with st.expander("Настроить коэффициенты сценариев", expanded=False):
        st.caption("Коэффициент = множитель от базового значения. 1.0 = без изменений.")
        new_defs = {}
        for sc_name, coeffs in scenario_defs.items():
            st.markdown(f"**{sc_name}**")
            cols = st.columns(6)
            new_coeffs = {}
            keys_labels = [
                ("price",      "Цена"),
                ("volume",     "Выпуск"),
                ("var_cost",   "Перем.изд."),
                ("fixed_cost", "Пост.изд."),
                ("rate",       "Ставка"),
                ("invest",     "Инвестиции"),
            ]
            for ci, (k, lbl) in enumerate(keys_labels):
                new_coeffs[k] = cols[ci].number_input(
                    lbl, value=coeffs[k], min_value=0.01, max_value=5.0, step=0.05,
                    key=f"sc_{sc_name}_{k}", format="%.2f"
                )
            new_defs[sc_name] = new_coeffs
        scenario_defs = new_defs

    # Считаем NPV для каждого сценария
    scenario_results = []
    for sc_name, coeffs in scenario_defs.items():
        p_sc = dict(sel_p)
        for k, mult in coeffs.items():
            p_sc[k] = sel_p[k] * mult
        p_sc["rate"]      = max(p_sc["rate"],      0.01)
        p_sc["inflation"] = max(p_sc["inflation"],  0.01)
        cfs_sc = build_cash_flows(p_sc)
        npv_sc = calc_npv(cfs_sc, p_sc["invest"], p_sc["rate"])
        irr_sc = calc_irr(cfs_sc, p_sc["invest"])
        pi_sc  = calc_pi (cfs_sc, p_sc["invest"], p_sc["rate"])
        scenario_results.append({
            "Сценарий":  sc_name,
            "NPV, Р":    npv_sc,
            "IRR":       f"{irr_sc:.2f}%" if irr_sc else "н/д",
            "PI":        pi_sc,
            "Цена":      f"{p_sc['price']:.2f}",
            "Выпуск":    f"{p_sc['volume']:.0f}",
            "Ставка":    f"{p_sc['rate']:.1f}%",
        })

    # Таблица сценариев
    df_sc = pd.DataFrame(scenario_results)

    def style_sc_npv(v):
        return "color:#1e3a5f;font-weight:600" if v >= 0 else "color:#a03020;font-weight:600"

    try:
        df_sc_styled = df_sc.style.map(style_sc_npv, subset=["NPV, Р"]) \
                           .format({"NPV, Р": lambda v: _n(v, 0), "PI": "{:.3f}"})
    except AttributeError:
        df_sc_styled = df_sc.style.applymap(style_sc_npv, subset=["NPV, Р"]) \
                           .format({"NPV, Р": lambda v: _n(v, 0), "PI": "{:.3f}"})

    st.dataframe(df_sc_styled, use_container_width=True, hide_index=True)

    # График сценариев
    sc_names = [s["Сценарий"] for s in scenario_results]
    sc_npvs  = [s["NPV, Р"]   for s in scenario_results]
    sc_colors = ["#a03020", "#4a6fa5", "#1e3a5f"]

    fig_sc = go.Figure(go.Bar(
        x=sc_names,
        y=sc_npvs,
        marker_color=sc_colors,
        text=[f"{_n(v, 0)} Р" for v in sc_npvs],
        textposition="outside",
        width=0.45,
    ))
    fig_sc.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
    fig_sc.update_layout(
        title=f"NPV по сценариям — {sel_name}",
        height=340, margin=dict(t=50, b=20),
        plot_bgcolor="white",
        yaxis=dict(title="NPV, Р", gridcolor="#eee"),
        showlegend=False,
    )
    st.plotly_chart(fig_sc, use_container_width=True, key="fig_sc")

    st.divider()

    # ══════════════════════════════════════════
    # БЛОК 3 — ВЕРОЯТНОСТНЫЙ АНАЛИЗ (Монте-Карло)
    # ══════════════════════════════════════════
    st.markdown('<div class="section-header">3. Вероятностный анализ (метод Монте-Карло)</div>',
                unsafe_allow_html=True)
    st.markdown(
        "Параметры проекта моделируются как случайные величины. "
        "Метод позволяет оценить **распределение NPV** и вероятность того, "
        "что проект окажется убыточным."
    )

    col_mc1, col_mc2 = st.columns(2)
    with col_mc1:
        n_simulations = st.select_slider(
            "Число симуляций",
            options=[500, 1000, 2000, 5000, 10000],
            value=2000,
        )
    with col_mc2:
        price_std  = st.slider("Разброс цены (σ, %)", 1, 30, 10,
                                help="Стандартное отклонение цены в % от базового значения")
        volume_std = st.slider("Разброс выпуска (σ, %)", 1, 30, 10)

    run_mc = st.button("Запустить симуляцию Монте-Карло", type="primary")

    if run_mc:
        import random, math
        random.seed(42)

        def rand_normal(mean, std_pct):
            """Случайная величина: нормальное распределение."""
            sigma = mean * std_pct / 100
            # Box-Muller
            u1 = max(random.random(), 1e-10)
            u2 = random.random()
            z  = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
            return mean + sigma * z

        npv_simulations = []
        for _ in range(n_simulations):
            p_mc = dict(sel_p)
            p_mc["price"]  = max(rand_normal(sel_p["price"],  price_std),  0.01)
            p_mc["volume"] = max(rand_normal(sel_p["volume"], volume_std), 1.0)
            cfs_mc = build_cash_flows(p_mc)
            npv_mc = calc_npv(cfs_mc, p_mc["invest"], p_mc["rate"])
            npv_simulations.append(npv_mc)

        npv_arr     = sorted(npv_simulations)
        mean_npv    = sum(npv_arr) / len(npv_arr)
        n           = len(npv_arr)
        std_npv     = math.sqrt(sum((x - mean_npv) ** 2 for x in npv_arr) / n)
        prob_loss   = sum(1 for v in npv_arr if v < 0) / n * 100
        npv_5pct    = npv_arr[int(n * 0.05)]
        npv_95pct   = npv_arr[int(n * 0.95)]

        # Метрики
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        mc1.metric("Среднее NPV",    f"{_n(mean_npv, 0)} Р")
        mc2.metric("Ст. отклонение", f"{_n(std_npv, 0)} Р")
        mc3.metric("P(NPV < 0)",     f"{prob_loss:.1f}%",
                   delta="риск убытка", delta_color="inverse")
        mc4.metric("90% интервал — от", f"{_n(npv_5pct, 0)} Р")
        mc5.metric("90% интервал — до", f"{_n(npv_95pct, 0)} Р")

        # Гистограмма
        # Разбиваем на 40 бинов вручную (без numpy)
        n_bins   = 40
        min_val  = npv_arr[0]
        max_val  = npv_arr[-1]
        bin_w    = (max_val - min_val) / n_bins if max_val != min_val else 1
        bins     = [min_val + i * bin_w for i in range(n_bins + 1)]
        counts   = [0] * n_bins
        for v in npv_arr:
            idx = min(int((v - min_val) / bin_w), n_bins - 1)
            counts[idx] += 1
        bin_centers = [(bins[i] + bins[i+1]) / 2 for i in range(n_bins)]
        bin_colors  = ["#a03020" if c < 0 else "#1e3a5f" for c in bin_centers]

        fig_mc = go.Figure()
        fig_mc.add_trace(go.Bar(
            x=bin_centers,
            y=counts,
            marker_color=bin_colors,
            width=bin_w * 0.9,
            name="Частота",
            hovertemplate="NPV ≈ %{_n(x, 0)} Р<br>Частота: %{y}<extra></extra>",
        ))
        fig_mc.add_vline(x=0, line_dash="dash", line_color="black",  line_width=2,
                         annotation_text="NPV=0", annotation_position="top right")
        fig_mc.add_vline(x=mean_npv, line_dash="dot", line_color="#c8773a", line_width=2,
                         annotation_text=f"Среднее={_n(mean_npv, 0)}",
                         annotation_position="top left")
        fig_mc.add_vrect(x0=npv_5pct, x1=npv_95pct,
                         fillcolor="#4a6fa5", opacity=0.08,
                         annotation_text="90% доверит. интервал",
                         annotation_position="top left")
        fig_mc.update_layout(
            title=f"Распределение NPV — {n_simulations} симуляций Монте-Карло",
            height=380, margin=dict(t=50, b=20),
            plot_bgcolor="white",
            xaxis=dict(title="NPV, Р", gridcolor="#eee"),
            yaxis=dict(title="Число симуляций", gridcolor="#eee"),
            showlegend=False,
        )
        st.plotly_chart(fig_mc, use_container_width=True, key="fig_mc")

        # Вывод по рискам
        if prob_loss < 10:
            risk_label = "Низкий риск"
            risk_text  = (
                f"Вероятность убытка составляет {prob_loss:.1f}% — проект устойчив. "
                f"Среднее NPV ({_n(mean_npv, 0)} Р) значительно выше нуля."
            )
            risk_css = "advice-box good"
        elif prob_loss < 30:
            risk_label = "Умеренный риск"
            risk_text  = (
                f"Вероятность убытка {prob_loss:.1f}% — приемлемый уровень риска. "
                f"Рекомендуется контролировать параметры с высокой эластичностью."
            )
            risk_css = "advice-box"
        else:
            risk_label = "Высокий риск"
            risk_text  = (
                f"Вероятность убытка {prob_loss:.1f}% — высокий риск. "
                f"Проект чувствителен к изменению входных параметров. "
                f"Рекомендуется пересмотреть параметры или отказаться от инвестиций."
            )
            risk_css = "advice-box"

        st.markdown(
            f'<div class="{risk_css}"><b>{risk_label}</b><br>{risk_text}</div>',
            unsafe_allow_html=True
        )

    st.divider()

    # ══════════════════════════════════════════
    # БЛОК 4 — СРАВНЕНИЕ РИСКОВ ВСЕХ ПРОЕКТОВ
    # ══════════════════════════════════════════
    st.markdown('<div class="section-header">4. Сравнение устойчивости всех проектов</div>',
                unsafe_allow_html=True)
    st.markdown(
        "Для каждого проекта рассчитывается критическое отклонение цены — "
        "при каком падении цены NPV уходит в ноль."
    )

    compare_rows = []
    for r in results_r:
        p_ = r["params"]
        # Ищем критическое отклонение цены
        crit_price = None
        for dev in range(1, 101):
            p_t = dict(p_); p_t["price"] = p_["price"] * (1 - dev / 100)
            npv_t = calc_npv(build_cash_flows(p_t), p_t["invest"], p_t["rate"])
            if (r["npv"] > 0 and npv_t <= 0) or (r["npv"] < 0 and npv_t >= 0):
                crit_price = dev
                break

        # Запас прочности по объёму
        bep_ = calc_bep(p_)
        safety = (1 - bep_ / p_["volume"]) * 100 if bep_ != float("inf") else -999

        risk_lvl = (
            "Высокий"  if (crit_price is not None and crit_price <= 10) or safety < 0 else
            "Средний"  if (crit_price is not None and crit_price <= 25) or safety < 20 else
            "Низкий"
        )

        compare_rows.append({
            "Проект":                 r["name"],
            "Базовый NPV, Р":        f"{_n(r['npv'], 0)}",
            "Критич. падение цены":   f"−{crit_price}%" if crit_price else "> −100%",
            "Запас прочности (BEP)":  f"{safety:.1f}%" if safety > -999 else "отриц.",
            "Уровень риска":          risk_lvl,
        })

    st.dataframe(pd.DataFrame(compare_rows), use_container_width=True, hide_index=True)

    # Radar chart — сравнение по нескольким осям риска
    if len(results_r) >= 2:
        st.markdown("**Профиль риска проектов** (нормализованные показатели, выше = лучше)")

        radar_categories = [
            "NPV (норм.)", "PI (норм.)", "Запас BEP", "Устойч. цены", "DPP (норм.)"
        ]

        def safe_norm(vals):
            """Нормализует список в диапазон 0.1..1.0."""
            mn, mx = min(vals), max(vals)
            if mx == mn:
                return [0.5] * len(vals)
            return [0.1 + 0.9 * (v - mn) / (mx - mn) for v in vals]



        raw_npv  = [r["npv"]  for r in results_r]
        raw_pi   = [r["pi"]   for r in results_r]
        raw_dpp  = [-(r["dpp"] if r["dpp"] else r["years"] * 1.5) for r in results_r]

        raw_bep_safety = []
        raw_crit_price = []
        for r in results_r:
            p_ = r["params"]
            bep_ = calc_bep(p_)
            safety_ = (1 - bep_ / p_["volume"]) * 100 if bep_ != float("inf") else -50
            raw_bep_safety.append(safety_)
            # Критичность цены
            cp = 100
            for dev in range(1, 101):
                p_t = dict(p_); p_t["price"] = p_["price"] * (1 - dev / 100)
                npv_t = calc_npv(build_cash_flows(p_t), p_t["invest"], p_t["rate"])
                if (r["npv"] > 0 and npv_t <= 0) or (r["npv"] < 0 and npv_t >= 0):
                    cp = dev
                    break
            raw_crit_price.append(cp)

        norm_npv   = safe_norm(raw_npv)
        norm_pi    = safe_norm(raw_pi)
        norm_bep   = safe_norm(raw_bep_safety)
        norm_crit  = safe_norm(raw_crit_price)
        norm_dpp   = safe_norm(raw_dpp)

        fig_radar = go.Figure()
        for ri, r in enumerate(results_r):
            vals = [
                norm_npv[ri], norm_pi[ri], norm_bep[ri],
                norm_crit[ri], norm_dpp[ri], norm_npv[ri],  # замыкаем фигуру
            ]
            cats = radar_categories + [radar_categories[0]]
            fig_radar.add_trace(go.Scatterpolar(
                r=vals, theta=cats,
                fill="toself",
                name=r["name"],
                line=dict(color=COLORS[ri % len(COLORS)]),
                opacity=0.7,
            ))

        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            title="Радарная диаграмма рисков проектов",
            height=440,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15),
        )
        st.plotly_chart(fig_radar, use_container_width=True, key="fig_radar")