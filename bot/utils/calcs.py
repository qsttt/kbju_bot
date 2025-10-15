from __future__ import annotations

def calc_bmr(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    if sex == "male":
        return 10*weight_kg + 6.25*height_cm - 5*age + 5
    else:
        return 10*weight_kg + 6.25*height_cm - 5*age - 161

def calc_tdee(bmr: float, pal: float) -> float:
    return bmr * pal

# goal: lose/maintain/gain
def calc_targets(tdee: float, goal: str) -> dict:
    if goal == "lose":
        kcal = tdee * 0.7
        ratios = (0.30, 0.25, 0.45)
    elif goal == "gain":
        kcal = tdee * 1.15
        ratios = (0.25, 0.30, 0.45)
    else:
        kcal = tdee
        ratios = (0.25, 0.30, 0.45)
    p_kcal, f_kcal, c_kcal = (kcal*r for r in ratios)
    protein = p_kcal / 4
    fat = f_kcal / 9
    carbs = c_kcal / 4
    return {"kcal": round(kcal), "p": round(protein), "f": round(fat), "c": round(carbs)}