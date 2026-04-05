from dataclasses import dataclass


@dataclass
class IngredientAmount:
    name: str
    amount: float
    unit: str = ""


def scale_ingredients(ingredients: list[IngredientAmount], reference_name: str, new_amount: float) -> list[IngredientAmount]:
    if not ingredients:
        raise ValueError("ingredients cannot be empty")

    reference = next((ing for ing in ingredients if ing.name == reference_name), None)
    if reference is None:
        raise ValueError("reference ingredient not found")
    if reference.amount == 0:
        raise ValueError("reference amount cannot be zero")

    factor = new_amount / reference.amount
    return [IngredientAmount(name=i.name, amount=i.amount * factor, unit=i.unit) for i in ingredients]
