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

    def test_raises_when_reference_missing(self):
        ingredients = [IngredientAmount(name="Mel", amount=500, unit="g")]

        with self.assertRaises(ValueError):
            scale_ingredients(ingredients, reference_name="Sukker", new_amount=400)


if __name__ == "__main__":
    unittest.main()
