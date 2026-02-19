import json
import tkinter as tk
from dataclasses import dataclass, asdict
from pathlib import Path
from tkinter import messagebox, ttk

from recipe_logic import IngredientAmount, scale_ingredients


DATA_FILE = Path("recipes.json")


@dataclass
class Ingredient:
    name: str
    amount: float
    unit: str


@dataclass
class Recipe:
    name: str
    instructions: str
    ingredients: list[Ingredient]


class RecipeStore:
    def __init__(self, path: Path = DATA_FILE) -> None:
        self.path = path
        self.recipes: list[Recipe] = []
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.recipes = []
            return

        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.recipes = [
            Recipe(
                name=item["name"],
                instructions=item["instructions"],
                ingredients=[Ingredient(**ing) for ing in item["ingredients"]],
            )
            for item in raw
        ]

    def save(self) -> None:
        payload = []
        for recipe in self.recipes:
            payload.append(
                {
                    "name": recipe.name,
                    "instructions": recipe.instructions,
                    "ingredients": [asdict(ing) for ing in recipe.ingredients],
                }
            )
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_recipe(self, recipe: Recipe) -> None:
        self.recipes.append(recipe)
        self.save()


class RecipeApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Oppskriftsapp med forholdstall")
        self.root.geometry("900x550")

        self.store = RecipeStore()
        self.ingredients_buffer: list[Ingredient] = []

        self._build_layout()
        self._refresh_recipe_list()

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        left = ttk.LabelFrame(container, text="Ny oppskrift", padding=10)
        right = ttk.LabelFrame(container, text="Bruk oppskrift", padding=10)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(left, text="Navn på rett").grid(row=0, column=0, sticky="w")
        self.recipe_name = ttk.Entry(left, width=40)
        self.recipe_name.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 8))

        ttk.Label(left, text="Ingrediens").grid(row=2, column=0, sticky="w")
        ttk.Label(left, text="Mengde").grid(row=2, column=1, sticky="w")
        ttk.Label(left, text="Enhet").grid(row=2, column=2, sticky="w")

        self.ing_name = ttk.Entry(left)
        self.ing_amount = ttk.Entry(left)
        self.ing_unit = ttk.Entry(left)
        self.ing_name.grid(row=3, column=0, sticky="ew", padx=(0, 5))
        self.ing_amount.grid(row=3, column=1, sticky="ew", padx=(0, 5))
        self.ing_unit.grid(row=3, column=2, sticky="ew")

        ttk.Button(left, text="Legg til ingrediens", command=self.add_ingredient).grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=8
        )

        self.ing_list = tk.Listbox(left, height=8)
        self.ing_list.grid(row=5, column=0, columnspan=3, sticky="nsew")

        ttk.Label(left, text="Instruksjoner").grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 0))
        self.instructions = tk.Text(left, height=8)
        self.instructions.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(0, 8))

        ttk.Button(left, text="Lagre oppskrift", command=self.save_recipe).grid(
            row=8, column=0, columnspan=3, sticky="ew"
        )

        left.columnconfigure(0, weight=2)
        left.columnconfigure(1, weight=1)
        left.columnconfigure(2, weight=1)
        left.rowconfigure(5, weight=1)
        left.rowconfigure(7, weight=1)

        ttk.Label(right, text="Velg oppskrift").grid(row=0, column=0, sticky="w")
        self.recipe_combo = ttk.Combobox(right, state="readonly")
        self.recipe_combo.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.recipe_combo.bind("<<ComboboxSelected>>", lambda _e: self.show_recipe())

        ttk.Label(right, text="Ingrediens som styrer skalering").grid(row=2, column=0, sticky="w")
        self.reference_combo = ttk.Combobox(right, state="readonly")
        self.reference_combo.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(right, text="Ny mengde for valgt ingrediens").grid(row=4, column=0, sticky="w")
        self.new_amount = ttk.Entry(right)
        self.new_amount.grid(row=5, column=0, sticky="ew", pady=(0, 8))

        ttk.Button(right, text="Beregn nye mengder", command=self.recalculate).grid(
            row=6, column=0, sticky="ew", pady=(0, 8)
        )

        self.output = tk.Text(right, height=18)
        self.output.grid(row=7, column=0, sticky="nsew")

        right.columnconfigure(0, weight=1)
        right.rowconfigure(7, weight=1)

    def add_ingredient(self) -> None:
        name = self.ing_name.get().strip()
        unit = self.ing_unit.get().strip()
        try:
            amount = float(self.ing_amount.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Ugyldig mengde", "Mengde må være et tall.")
            return

        if not name:
            messagebox.showerror("Mangler data", "Ingrediensnavn må fylles ut.")
            return

        ingredient = Ingredient(name=name, amount=amount, unit=unit)
        self.ingredients_buffer.append(ingredient)
        self.ing_list.insert(tk.END, f"{name}: {amount:g} {unit}".strip())

        self.ing_name.delete(0, tk.END)
        self.ing_amount.delete(0, tk.END)
        self.ing_unit.delete(0, tk.END)

    def save_recipe(self) -> None:
        name = self.recipe_name.get().strip()
        instructions = self.instructions.get("1.0", tk.END).strip()

        if not name:
            messagebox.showerror("Mangler navn", "Oppskriften må ha et navn.")
            return
        if not self.ingredients_buffer:
            messagebox.showerror("Mangler ingredienser", "Legg til minst én ingrediens.")
            return

        recipe = Recipe(name=name, instructions=instructions, ingredients=list(self.ingredients_buffer))
        self.store.add_recipe(recipe)
        self._clear_create_form()
        self._refresh_recipe_list()
        messagebox.showinfo("Lagret", f"Oppskriften '{name}' ble lagret.")

    def _clear_create_form(self) -> None:
        self.recipe_name.delete(0, tk.END)
        self.instructions.delete("1.0", tk.END)
        self.ing_list.delete(0, tk.END)
        self.ingredients_buffer = []

    def _refresh_recipe_list(self) -> None:
        names = [recipe.name for recipe in self.store.recipes]
        self.recipe_combo["values"] = names
        if names:
            self.recipe_combo.current(0)
            self.show_recipe()

    def _selected_recipe(self) -> Recipe | None:
        selected_name = self.recipe_combo.get()
        for recipe in self.store.recipes:
            if recipe.name == selected_name:
                return recipe
        return None

    def show_recipe(self) -> None:
        recipe = self._selected_recipe()
        if recipe is None:
            return

        self.reference_combo["values"] = [ing.name for ing in recipe.ingredients]
        if recipe.ingredients:
            self.reference_combo.current(0)

        lines = [f"Oppskrift: {recipe.name}\n", "Ingredienser:"]
        for ing in recipe.ingredients:
            lines.append(f"- {ing.name}: {ing.amount:g} {ing.unit}".strip())

        lines.append("\nInstruksjoner:")
        lines.append(recipe.instructions or "(ingen)")

        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, "\n".join(lines))

    def recalculate(self) -> None:
        recipe = self._selected_recipe()
        if recipe is None:
            return

        reference_name = self.reference_combo.get()
        reference = next((ing for ing in recipe.ingredients if ing.name == reference_name), None)
        if reference is None:
            messagebox.showerror("Mangler ingrediens", "Velg en ingrediens å skalere fra.")
            return

        try:
            new_reference_amount = float(self.new_amount.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Ugyldig mengde", "Ny mengde må være et tall.")
            return

        try:
            scaled_ingredients = scale_ingredients(
                [IngredientAmount(name=i.name, amount=i.amount, unit=i.unit) for i in recipe.ingredients],
                reference_name=reference.name,
                new_amount=new_reference_amount,
            )
        except ValueError as error:
            messagebox.showerror("Skaleringsfeil", str(error))
            return

        factor = new_reference_amount / reference.amount
        updated_lines = [
            f"Skalert oppskrift: {recipe.name}",
            f"Basis: {reference.name} fra {reference.amount:g} til {new_reference_amount:g} (faktor {factor:.3f})",
            "",
            "Nye mengder:",
        ]

        for ing in scaled_ingredients:
            updated_lines.append(f"- {ing.name}: {ing.amount:g} {ing.unit}".strip())

        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, "\n".join(updated_lines))


def main() -> None:
    root = tk.Tk()
    RecipeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
