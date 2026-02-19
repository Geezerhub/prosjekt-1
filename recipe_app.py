import json
import os
import tempfile
import tkinter as tk
from dataclasses import dataclass, asdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from export_utils import write_simple_text_pdf
from recipe_logic import IngredientAmount, scale_ingredients


DATA_FILE = Path("recipes.json")
ICON_FILE = Path("assets/app_icon.ppm")


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

    def find_index(self, name: str) -> int | None:
        for index, recipe in enumerate(self.recipes):
            if recipe.name == name:
                return index
        return None

    def add_recipe(self, recipe: Recipe) -> None:
        self.recipes.append(recipe)
        self.save()

    def replace_recipe(self, original_name: str, updated_recipe: Recipe) -> bool:
        index = self.find_index(original_name)
        if index is None:
            return False
        self.recipes[index] = updated_recipe
        self.save()
        return True


class RecipeApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Oppskriftsapp med forholdstall")
        self.root.geometry("950x650")
        self._set_app_icon()

        self.store = RecipeStore()
        self.ingredients_buffer: list[Ingredient] = []
        self.editing_original_name: str | None = None

        self._build_layout()
        self._refresh_recipe_list()

    def _set_app_icon(self) -> None:
        if ICON_FILE.exists():
            try:
                icon = tk.PhotoImage(file=str(ICON_FILE))
                self.root.iconphoto(True, icon)
                self.root._icon_ref = icon
            except tk.TclError:
                pass

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        self.left_group = ttk.LabelFrame(container, text="Ny oppskrift", padding=10)
        right = ttk.LabelFrame(container, text="Bruk oppskrift", padding=10)
        self.left_group.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(self.left_group, text="Navn på rett").grid(row=0, column=0, sticky="w")
        self.recipe_name = ttk.Entry(self.left_group, width=40)
        self.recipe_name.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 8))

        ttk.Label(self.left_group, text="Ingrediens").grid(row=2, column=0, sticky="w")
        ttk.Label(self.left_group, text="Mengde").grid(row=2, column=1, sticky="w")
        ttk.Label(self.left_group, text="Enhet").grid(row=2, column=2, sticky="w")

        self.ing_name = ttk.Entry(self.left_group)
        self.ing_amount = ttk.Entry(self.left_group)
        self.ing_unit = ttk.Entry(self.left_group)
        self.ing_name.grid(row=3, column=0, sticky="ew", padx=(0, 5))
        self.ing_amount.grid(row=3, column=1, sticky="ew", padx=(0, 5))
        self.ing_unit.grid(row=3, column=2, sticky="ew")

        ttk.Button(self.left_group, text="Legg til ingrediens", command=self.add_ingredient).grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=8
        )

        self.ing_list = tk.Listbox(self.left_group, height=8)
        self.ing_list.grid(row=5, column=0, columnspan=3, sticky="nsew")

        ttk.Label(self.left_group, text="Instruksjoner").grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 0))
        self.instructions = tk.Text(self.left_group, height=8)
        self.instructions.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(0, 8))

        self.save_button = ttk.Button(self.left_group, text="Lagre oppskrift", command=self.save_recipe)
        self.save_button.grid(row=8, column=0, columnspan=2, sticky="ew")
        self.cancel_edit_button = ttk.Button(
            self.left_group, text="Avbryt redigering", command=self.cancel_edit, state=tk.DISABLED
        )
        self.cancel_edit_button.grid(row=8, column=2, sticky="ew", padx=(5, 0))

        self.left_group.columnconfigure(0, weight=2)
        self.left_group.columnconfigure(1, weight=1)
        self.left_group.columnconfigure(2, weight=1)
        self.left_group.rowconfigure(5, weight=1)
        self.left_group.rowconfigure(7, weight=1)

        ttk.Label(right, text="Velg oppskrift").grid(row=0, column=0, sticky="w")
        self.recipe_combo = ttk.Combobox(right, state="readonly")
        self.recipe_combo.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.recipe_combo.bind("<<ComboboxSelected>>", lambda _e: self.show_recipe())

        ttk.Button(right, text="Rediger valgt oppskrift", command=self.load_selected_for_edit).grid(
            row=2, column=0, sticky="ew", pady=(0, 8)
        )

        ttk.Label(right, text="Ingrediens som styrer skalering").grid(row=3, column=0, sticky="w")
        self.reference_combo = ttk.Combobox(right, state="readonly")
        self.reference_combo.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(right, text="Ny mengde for valgt ingrediens").grid(row=5, column=0, sticky="w")
        self.new_amount = ttk.Entry(right)
        self.new_amount.grid(row=6, column=0, sticky="ew", pady=(0, 8))

        ttk.Button(right, text="Beregn nye mengder", command=self.recalculate).grid(
            row=7, column=0, sticky="ew", pady=(0, 8)
        )

        export_row = ttk.Frame(right)
        export_row.grid(row=8, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(export_row, text="Lagre som .txt", command=self.export_txt).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(export_row, text="Lagre som .pdf", command=self.export_pdf).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(export_row, text="Skriv ut", command=self.print_current).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.output = tk.Text(right, height=18)
        self.output.grid(row=9, column=0, sticky="nsew")

        right.columnconfigure(0, weight=1)
        right.rowconfigure(9, weight=1)

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

        if self.editing_original_name is None:
            if self.store.find_index(name) is not None:
                messagebox.showerror("Navn i bruk", "Det finnes allerede en oppskrift med dette navnet.")
                return
            self.store.add_recipe(recipe)
            saved_name = name
            messagebox.showinfo("Lagret", f"Oppskriften '{name}' ble lagret.")
        else:
            if name != self.editing_original_name and self.store.find_index(name) is not None:
                messagebox.showerror("Navn i bruk", "Velg et annet navn, dette brukes allerede.")
                return

            updated = self.store.replace_recipe(self.editing_original_name, recipe)
            if not updated:
                messagebox.showerror("Fant ikke", "Kunne ikke oppdatere oppskriften.")
                return
            saved_name = name
            messagebox.showinfo("Oppdatert", f"Oppskriften '{name}' ble oppdatert.")

        self._clear_create_form()
        self._set_edit_mode(None)
        self._refresh_recipe_list(select_name=saved_name)

    def _clear_create_form(self) -> None:
        self.recipe_name.delete(0, tk.END)
        self.instructions.delete("1.0", tk.END)
        self.ing_list.delete(0, tk.END)
        self.ingredients_buffer = []

    def _set_edit_mode(self, original_name: str | None) -> None:
        self.editing_original_name = original_name
        if original_name is None:
            self.left_group.configure(text="Ny oppskrift")
            self.save_button.configure(text="Lagre oppskrift")
            self.cancel_edit_button.configure(state=tk.DISABLED)
        else:
            self.left_group.configure(text=f"Rediger oppskrift: {original_name}")
            self.save_button.configure(text="Oppdater oppskrift")
            self.cancel_edit_button.configure(state=tk.NORMAL)

    def cancel_edit(self) -> None:
        self._clear_create_form()
        self._set_edit_mode(None)

    def load_selected_for_edit(self) -> None:
        recipe = self._selected_recipe()
        if recipe is None:
            messagebox.showerror("Ingen valgt", "Velg en oppskrift først.")
            return

        self._clear_create_form()
        self._set_edit_mode(recipe.name)

        self.recipe_name.insert(0, recipe.name)
        self.instructions.insert("1.0", recipe.instructions)
        for ing in recipe.ingredients:
            copy_ing = Ingredient(name=ing.name, amount=ing.amount, unit=ing.unit)
            self.ingredients_buffer.append(copy_ing)
            self.ing_list.insert(tk.END, f"{copy_ing.name}: {copy_ing.amount:g} {copy_ing.unit}".strip())

    def _refresh_recipe_list(self, select_name: str | None = None) -> None:
        names = [recipe.name for recipe in self.store.recipes]
        self.recipe_combo["values"] = names
        if not names:
            self.output.delete("1.0", tk.END)
            self.reference_combo["values"] = []
            return

        if select_name and select_name in names:
            self.recipe_combo.current(names.index(select_name))
        elif self.recipe_combo.get() in names:
            self.recipe_combo.current(names.index(self.recipe_combo.get()))
        else:
            self.recipe_combo.current(0)
        self.show_recipe()

    def _selected_recipe(self) -> Recipe | None:
        selected_name = self.recipe_combo.get()
        for recipe in self.store.recipes:
            if recipe.name == selected_name:
                return recipe
        return None

    def _build_recipe_text(self, recipe: Recipe) -> str:
        lines = [f"Oppskrift: {recipe.name}", "", "Ingredienser:"]
        for ing in recipe.ingredients:
            lines.append(f"- {ing.name}: {ing.amount:g} {ing.unit}".strip())
        lines.extend(["", "Instruksjoner:", recipe.instructions or "(ingen)"])
        return "\n".join(lines)

    def _current_output_text(self) -> str:
        text = self.output.get("1.0", tk.END).strip()
        if text:
            return text
        recipe = self._selected_recipe()
        if recipe is None:
            return ""
        return self._build_recipe_text(recipe)

    def show_recipe(self) -> None:
        recipe = self._selected_recipe()
        if recipe is None:
            return

        self.reference_combo["values"] = [ing.name for ing in recipe.ingredients]
        if recipe.ingredients:
            self.reference_combo.current(0)

        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, self._build_recipe_text(recipe))

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

    def export_txt(self) -> None:
        content = self._current_output_text()
        if not content:
            messagebox.showerror("Ingen data", "Velg eller lag en oppskrift først.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Tekstfil", "*.txt")],
            title="Lagre oppskrift som tekst",
        )
        if not file_path:
            return

        Path(file_path).write_text(content, encoding="utf-8")
        messagebox.showinfo("Lagret", f"Oppskriften ble lagret som tekst:\n{file_path}")

    def export_pdf(self) -> None:
        content = self._current_output_text()
        if not content:
            messagebox.showerror("Ingen data", "Velg eller lag en oppskrift først.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            title="Lagre oppskrift som PDF",
        )
        if not file_path:
            return

        write_simple_text_pdf(content, Path(file_path), title="Oppskrift")
        messagebox.showinfo("Lagret", f"Oppskriften ble lagret som PDF:\n{file_path}")

    def print_current(self) -> None:
        content = self._current_output_text()
        if not content:
            messagebox.showerror("Ingen data", "Velg eller lag en oppskrift først.")
            return

        if os.name != "nt":
            messagebox.showwarning(
                "Kun Windows",
                "Direkte utskrift støttes kun på Windows i denne versjonen. Bruk 'Lagre som .pdf' ellers.",
            )
            return

        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as handle:
            handle.write(content)
            temp_path = handle.name

        try:
            os.startfile(temp_path, "print")
            messagebox.showinfo("Utskrift sendt", "Oppskriften er sendt til standardskriveren i Windows.")
        except OSError as error:
            messagebox.showerror("Utskriftsfeil", f"Kunne ikke skrive ut: {error}")


def main() -> None:
    root = tk.Tk()
    RecipeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
