import tempfile
import unittest
from pathlib import Path

from recipe_app import Ingredient, Recipe, RecipeStore


class FailingSaveStore(RecipeStore):
    def save(self) -> None:  # type: ignore[override]
        raise OSError("disk full")


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

    def test_load_handles_invalid_json_without_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "recipes.json"
            db.write_text("{ikke gyldig json", encoding="utf-8")

            store = RecipeStore(path=db)

            self.assertEqual([], store.recipes)
            self.assertIsNotNone(store.load_error_message)

    def test_load_handles_invalid_structure_without_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "recipes.json"
            db.write_text('[{"name":"X","instructions":"Y","ingredients":"bad"}]', encoding="utf-8")

            store = RecipeStore(path=db)

            self.assertEqual([], store.recipes)
            self.assertIsNotNone(store.load_error_message)

    def test_add_recipe_rolls_back_on_save_error(self):
        store = FailingSaveStore(path=Path("/tmp/not-used.json"))

        with self.assertRaises(OSError):
            store.add_recipe(Recipe(name="A", instructions="B", ingredients=[Ingredient("Mel", 1, "g")]))

        self.assertEqual([], store.recipes)

    def test_replace_recipe_rolls_back_on_save_error(self):
        store = FailingSaveStore(path=Path("/tmp/not-used.json"))
        store.recipes = [Recipe(name="A", instructions="Old", ingredients=[Ingredient("Mel", 1, "g")])]

        with self.assertRaises(OSError):
            store.replace_recipe("A", Recipe(name="A", instructions="New", ingredients=[Ingredient("Mel", 2, "g")]))

        self.assertEqual("Old", store.recipes[0].instructions)


if __name__ == "__main__":
    unittest.main()
