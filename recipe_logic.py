from dataclasses import dataclass


@dataclass
class IngredientAmount:
    name: str
    amount: float
    unit: str = ""


NON_SCALING_UNITS = {"knep", "dæsj"}


def _normalize_unit(unit: str) -> str:
    return unit.strip().lower().rstrip(".")


def scale_ingredients(
    ingredients: list[IngredientAmount],
    reference_name: str,
    new_amount: float,
    non_scaling_units: set[str] | None = None,
) -> list[IngredientAmount]:
    if not ingredients:
        raise ValueError("ingredients cannot be empty")

    reference = next((ing for ing in ingredients if ing.name == reference_name), None)
    if reference is None:
        raise ValueError("reference ingredient not found")
    if reference.amount == 0:
        raise ValueError("reference amount cannot be zero")

    factor = new_amount / reference.amount

    resolved_non_scaling_units = {
        _normalize_unit(unit) for unit in (non_scaling_units if non_scaling_units is not None else NON_SCALING_UNITS)
    }

    scaled_ingredients: list[IngredientAmount] = []
    for ingredient in ingredients:
        if _normalize_unit(ingredient.unit) in resolved_non_scaling_units:
            scaled_amount = ingredient.amount
        else:
            scaled_amount = ingredient.amount * factor

        scaled_ingredients.append(IngredientAmount(name=ingredient.name, amount=scaled_amount, unit=ingredient.unit))

    return scaled_ingredients
