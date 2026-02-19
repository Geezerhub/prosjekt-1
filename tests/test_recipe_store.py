import tempfile
import unittest
from pathlib import Path

from recipe_app import Ingredient, Recipe, RecipeStore


class RecipeStoreTests(unittest.TestCase):
    def test_replace_recipe_updates_existing_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "recipes.json"
            store = RecipeStore(path=db)
            store.add_recipe(Recipe(name="Pannekaker", instructions="Stek", ingredients=[Ingredient("Mel", 300, "g")]))

            updated = store.replace_recipe(
                "Pannekaker",
                Recipe(name="Pannekaker", instructions="Stek rolig", ingredients=[Ingredient("Mel", 350, "g")]),
            )

            self.assertTrue(updated)
            reloaded = RecipeStore(path=db)
            self.assertEqual("Stek rolig", reloaded.recipes[0].instructions)
            self.assertEqual(350, reloaded.recipes[0].ingredients[0].amount)

    def test_replace_recipe_returns_false_if_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "recipes.json"
            store = RecipeStore(path=db)

            updated = store.replace_recipe(
                "Finnes ikke",
                Recipe(name="N", instructions="I", ingredients=[Ingredient("A", 1, "stk")]),
            )

            self.assertFalse(updated)


if __name__ == "__main__":
    unittest.main()
