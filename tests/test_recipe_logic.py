import unittest

from recipe_logic import IngredientAmount, scale_ingredients


class ScaleIngredientsTests(unittest.TestCase):
    def test_scales_all_ingredients_from_reference(self):
        ingredients = [
            IngredientAmount(name="Mel", amount=500, unit="g"),
            IngredientAmount(name="Vann", amount=300, unit="ml"),
            IngredientAmount(name="Salt", amount=10, unit="g"),
        ]

        scaled = scale_ingredients(ingredients, reference_name="Mel", new_amount=750)

        self.assertEqual(750, scaled[0].amount)
        self.assertEqual(450, scaled[1].amount)
        self.assertEqual(15, scaled[2].amount)

    def test_does_not_scale_knep_or_daesj_units(self):
        ingredients = [
            IngredientAmount(name="Mel", amount=500, unit="g"),
            IngredientAmount(name="Kanel", amount=1, unit="knep"),
            IngredientAmount(name="Saus", amount=2, unit="dæsj"),
        ]

        scaled = scale_ingredients(ingredients, reference_name="Mel", new_amount=1000)

        self.assertEqual(1000, scaled[0].amount)
        self.assertEqual(1, scaled[1].amount)
        self.assertEqual(2, scaled[2].amount)

    def test_raises_when_reference_missing(self):
        ingredients = [IngredientAmount(name="Mel", amount=500, unit="g")]

        with self.assertRaises(ValueError):
            scale_ingredients(ingredients, reference_name="Sukker", new_amount=400)

    def test_can_override_non_scaling_units_from_settings(self):
        ingredients = [
            IngredientAmount(name="Mel", amount=500, unit="g"),
            IngredientAmount(name="Vann", amount=3, unit="kopp"),
        ]

        scaled = scale_ingredients(
            ingredients,
            reference_name="Mel",
            new_amount=1000,
            non_scaling_units={"kopp"},
        )

        self.assertEqual(1000, scaled[0].amount)
        self.assertEqual(3, scaled[1].amount)


if __name__ == "__main__":
    unittest.main()
