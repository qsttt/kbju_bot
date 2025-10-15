from __future__ import annotations
import re

# единицы измерения (минимальный набор)
_UNITS = {
    'г': 'g', 'гр': 'g', 'гр.': 'g', 'грамм': 'g',
    'кг': 'kg',
    'мл': 'ml', 'л': 'l',
    'шт': 'pcs', 'штука': 'pcs', 'штуки': 'pcs'
}

# методы готовки
COOK_METHODS = {
    'сырая': 'raw', 'сырое': 'raw', 'raw': 'raw',
    'вареная': 'boiled', 'варёная': 'boiled', 'отварная': 'boiled', 'boiled': 'boiled',
    'жареная': 'fried', 'жаренная': 'fried', 'fried': 'fried',
    'запеченная': 'baked', 'запечённая': 'baked', 'baked': 'baked',
    'на гриле': 'grilled', 'гриль': 'grilled', 'grilled': 'grilled',
}

class Parsed:
    def __init__(
        self,
        title: str,
        amount_value: float | None,
        amount_unit: str | None,
        grams: float | None,
        kcal: float | None,
        p: float | None,
        f: float | None,
        c: float | None,
        is_cal_only: bool,
        method: str | None = None
    ):
        self.title = title
        self.amount_value = amount_value
        self.amount_unit = amount_unit
        self.grams = grams
        self.kcal = kcal
        self.p = p
        self.f = f
        self.c = c
        self.is_cal_only = is_cal_only
        self.method = method

def _guess_grams(amount_value: float | None, amount_unit: str | None) -> float | None:
    """Очень грубая эвристика, чтобы не падать, если нужно масштабировать БЖУ per 100g."""
    if amount_value is None or amount_unit is None:
        return None
    unit = amount_unit.lower()
    if unit in ('g',):
        return amount_value
    if unit in ('kg',):
        return amount_value * 1000
    if unit in ('ml',):
        # для воды/йогурта и т.п.  ~1 мл ≈ 1 г
        return amount_value
    if unit in ('l',):
        return amount_value * 1000
    if unit in ('pcs',):
        # по умолчанию не знаем массу штуки
        return None
    return None

def parse_line(text: str) -> Parsed:
    """
    Примеры:
      - 'куриная грудка варёная 140 г'
      - 'батончик 180 ккал'
      - 'творог 100 г б 18 ж 5 у 3'  (макросы пока не парсим детально в MVP)
    """
    t = (text or "").strip().lower()

    # 1) метод готовки
    method = None
    for k, v in COOK_METHODS.items():
        if re.search(rf"\b{k}\b", t, flags=re.I):
            method = v
            t = re.sub(rf"\b{k}\b", "", t, flags=re.I).strip()
            break

    # 2) количество и единицы
    amount_value, amount_unit = None, None
    m_qty = re.search(r"(\d+[.,]?\d*)\s*(г|гр|гр\.|грамм|кг|мл|л|шт|штука|штуки)\b", t)
    if m_qty:
        amount_value = float(m_qty.group(1).replace(",", "."))
        raw_unit = m_qty.group(2)
        amount_unit = _UNITS.get(raw_unit, raw_unit)
        t = re.sub(m_qty.group(0), "", t).strip()

    # 3) калории (если пользователь ввёл ккал прямо)
    kcal = None
    p = f = c = None
    is_cal_only = False
    m_kcal = re.search(r"(\d+[.,]?\d*)\s*(ккал|кал|cal)\b", t)
    if m_kcal:
        kcal = float(m_kcal.group(1).replace(",", "."))
        is_cal_only = True
        t = re.sub(m_kcal.group(0), "", t).strip()

    grams = _guess_grams(amount_value, amount_unit)

    # На этом этапе:
    #  - title = t (очищен от метода и количества)
    #  - если kcal указаны — is_cal_only=True
    #  - grams может быть None (если шт/нет единицы)
    return Parsed(
        title=t or "",
        amount_value=amount_value,
        amount_unit=amount_unit,
        grams=grams,
        kcal=kcal, p=p, f=f, c=c,
        is_cal_only=is_cal_only,
        method=method,
    )
