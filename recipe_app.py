import html
import json
import tempfile
import tkinter as tk
import webbrowser
from json import JSONDecodeError
from dataclasses import dataclass, asdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from recipe_logic import NON_SCALING_UNITS, IngredientAmount, scale_ingredients


DATA_FILE = Path("recipes.json")
SETTINGS_FILE = Path("settings.json")


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


@dataclass
class AppSettings:
    non_scaling_units: list[str]
    recipe_folder: str


class RecipeStore:
    def __init__(self, path: Path = DATA_FILE) -> None:
        self.path = path
        self.recipes: list[Recipe] = []
        self.load_error_message: str | None = None
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.recipes = []
            self.load_error_message = None
            return

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, JSONDecodeError) as error:
            self.recipes = []
            self.load_error_message = f"Kunne ikke lese lagret fil ({error})."
            return

        parsed: list[Recipe] = []
        try:
            for item in raw:
                ingredients: list[Ingredient] = []
                for ing in item["ingredients"]:
                    ingredients.append(
                        Ingredient(
                            name=str(ing["name"]),
                            amount=float(ing["amount"]),
                            unit=str(ing.get("unit", "")),
                        )
                    )
                parsed.append(
                    Recipe(
                        name=str(item["name"]),
                        instructions=str(item.get("instructions", "")),
                        ingredients=ingredients,
                    )
                )
        except (TypeError, KeyError, ValueError) as error:
            self.recipes = []
            self.load_error_message = f"Lagringsfilen har ugyldig format ({error})."
            return

        self.recipes = parsed
        self.load_error_message = None

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
        try:
            self.save()
        except OSError:
            self.recipes.pop()
            raise

    def replace_recipe(self, original_name: str, updated_recipe: Recipe) -> bool:
        index = self.find_index(original_name)
        if index is None:
            return False

        previous_recipe = self.recipes[index]
        self.recipes[index] = updated_recipe
        try:
            self.save()
        except OSError:
            self.recipes[index] = previous_recipe
            raise
        return True


class RecipeApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Oppskriftsapp med forholdstall")
        self.root.geometry("950x650")

        self.settings = self._load_settings()
        self.non_scaling_units = {unit.lower() for unit in self.settings.non_scaling_units}
        self.store = RecipeStore(path=self._recipe_file_path())
        self.ingredients_buffer: list[Ingredient] = []
        self.editing_original_name: str | None = None

        self._build_layout()
        self._refresh_recipe_list()

        if self.store.load_error_message:
            messagebox.showwarning("Problem med lagret fil", self.store.load_error_message)

    def _load_settings(self) -> AppSettings:
        default_folder = str(DATA_FILE.parent.resolve())
        defaults = AppSettings(non_scaling_units=sorted(NON_SCALING_UNITS), recipe_folder=default_folder)

        if not SETTINGS_FILE.exists():
            return defaults

        try:
            payload = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            units = payload.get("non_scaling_units", defaults.non_scaling_units)
            folder = payload.get("recipe_folder", defaults.recipe_folder)
            parsed_units = [str(unit).strip() for unit in units if str(unit).strip()]
            parsed_folder = str(folder).strip() or defaults.recipe_folder
            return AppSettings(non_scaling_units=parsed_units or defaults.non_scaling_units, recipe_folder=parsed_folder)
        except (OSError, JSONDecodeError, TypeError, ValueError):
            return defaults

    def _save_settings(self) -> None:
        payload = {
            "non_scaling_units": sorted(self.non_scaling_units),
            "recipe_folder": self.settings.recipe_folder,
        }
        SETTINGS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _recipe_file_path(self) -> Path:
        folder = Path(self.settings.recipe_folder).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        return folder / DATA_FILE.name

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
        self.ing_unit.bind("<FocusIn>", self._select_unit_text)
        self.ing_name.grid(row=3, column=0, sticky="ew", padx=(0, 5))
        self.ing_amount.grid(row=3, column=1, sticky="ew", padx=(0, 5))
        self.ing_unit.grid(row=3, column=2, sticky="ew")
        for entry in (self.ing_name, self.ing_amount, self.ing_unit):
            entry.bind("<Return>", self._add_ingredient_from_enter)
            entry.bind("<KP_Enter>", self._add_ingredient_from_enter)

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
        ttk.Button(export_row, text="Skriv ut", command=self.print_current).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.output = tk.Text(right, height=18)
        self.output.grid(row=9, column=0, sticky="nsew")

        settings_group = ttk.LabelFrame(right, text="Innstillinger", padding=8)
        settings_group.grid(row=10, column=0, sticky="ew", pady=(8, 0))

        ttk.Label(settings_group, text="Enheter som ikke skaleres (kommaseparert)").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        self.non_scaling_units_entry = ttk.Entry(settings_group)
        self.non_scaling_units_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 8))
        self.non_scaling_units_entry.insert(0, ", ".join(sorted(self.non_scaling_units)))

        ttk.Label(settings_group, text="Mappe for lagrede oppskrifter").grid(row=2, column=0, columnspan=2, sticky="w")
        self.recipe_folder_entry = ttk.Entry(settings_group)
        self.recipe_folder_entry.grid(row=3, column=0, sticky="ew", pady=(2, 8))
        self.recipe_folder_entry.insert(0, self.settings.recipe_folder)
        ttk.Button(settings_group, text="Velg mappe", command=self._choose_recipe_folder).grid(
            row=3, column=1, sticky="ew", padx=(6, 0)
        )

        ttk.Button(settings_group, text="Lagre innstillinger", command=self._apply_settings).grid(
            row=4, column=0, columnspan=2, sticky="ew"
        )
        settings_group.columnconfigure(0, weight=1)
        settings_group.columnconfigure(1, weight=0)

        right.columnconfigure(0, weight=1)
        right.rowconfigure(9, weight=1)

        self.root.bind_all("<Return>", self._on_enter_pressed, add="+")
        self.root.bind_all("<KP_Enter>", self._on_enter_pressed, add="+")

    def _add_ingredient_from_enter(self, _event: tk.Event) -> str:
        self.add_ingredient()
        return "break"

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
        self.ing_name.focus_set()
        self.ing_name.selection_range(0, tk.END)

    def _select_unit_text(self, _event: tk.Event) -> None:
        self.ing_unit.selection_range(0, tk.END)

    def _on_enter_pressed(self, _event: tk.Event) -> str | None:
        focused_widget = self.root.focus_get()
        if isinstance(focused_widget, tk.Text):
            return None

        target_widget = focused_widget
        if target_widget is None:
            pointer_x, pointer_y = self.root.winfo_pointerxy()
            target_widget = self.root.winfo_containing(pointer_x, pointer_y)

        if target_widget is None:
            return None

        target_widget.event_generate("<Button-1>")
        if hasattr(target_widget, "invoke"):
            target_widget.invoke()  # type: ignore[attr-defined]

        return "break"

    def _choose_recipe_folder(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.recipe_folder_entry.get().strip() or self.settings.recipe_folder)
        if selected:
            self.recipe_folder_entry.delete(0, tk.END)
            self.recipe_folder_entry.insert(0, selected)

    def _apply_settings(self) -> None:
        raw_units = self.non_scaling_units_entry.get().strip()
        parsed_units = {part.strip().lower().rstrip(".") for part in raw_units.split(",") if part.strip()}
        if not parsed_units:
            messagebox.showerror("Ugyldige enheter", "Legg inn minst én enhet som ikke skal skaleres.")
            return

        folder_text = self.recipe_folder_entry.get().strip()
        if not folder_text:
            messagebox.showerror("Ugyldig mappe", "Velg en mappe for lagrede oppskrifter.")
            return

        folder_path = Path(folder_text).expanduser()
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            messagebox.showerror("Mappefeil", f"Kunne ikke bruke mappen: {error}")
            return

        previous_recipe_name = self.recipe_combo.get()
        self.non_scaling_units = parsed_units
        self.settings = AppSettings(non_scaling_units=sorted(parsed_units), recipe_folder=str(folder_path))

        try:
            self._save_settings()
            self.store = RecipeStore(path=self._recipe_file_path())
        except OSError as error:
            messagebox.showerror("Lagringsfeil", f"Kunne ikke lagre innstillinger: {error}")
            return

        self.non_scaling_units_entry.delete(0, tk.END)
        self.non_scaling_units_entry.insert(0, ", ".join(sorted(self.non_scaling_units)))
        self.recipe_folder_entry.delete(0, tk.END)
        self.recipe_folder_entry.insert(0, self.settings.recipe_folder)

        self._refresh_recipe_list(select_name=previous_recipe_name or None)
        messagebox.showinfo("Innstillinger lagret", "Innstillingene ble oppdatert.")

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
            try:
                self.store.add_recipe(recipe)
            except OSError as error:
                messagebox.showerror("Lagringsfeil", f"Kunne ikke lagre oppskriften: {error}")
                return
            saved_name = name
            messagebox.showinfo("Lagret", f"Oppskriften '{name}' ble lagret.")
        else:
            if name != self.editing_original_name and self.store.find_index(name) is not None:
                messagebox.showerror("Navn i bruk", "Velg et annet navn, dette brukes allerede.")
                return

            try:
                updated = self.store.replace_recipe(self.editing_original_name, recipe)
            except OSError as error:
                messagebox.showerror("Lagringsfeil", f"Kunne ikke oppdatere oppskriften: {error}")
                return

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
                non_scaling_units=self.non_scaling_units,
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

    def print_current(self) -> None:
        content = self._current_output_text()
        if not content:
            messagebox.showerror("Ingen data", "Velg eller lag en oppskrift først.")
            return

        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as handle:
            escaped_content = html.escape(content).replace("\n", "<br>")
            handle.write(
                "<html><head><meta charset='utf-8'><title>Oppskrift</title></head>"
                "<body style='font-family:Segoe UI,Arial,sans-serif;padding:24px;'>"
                f"<pre style='white-space:pre-wrap;font-size:16px;line-height:1.4'>{escaped_content}</pre>"
                "<script>window.onload=function(){window.print();}</script>"
                "</body></html>"
            )
            temp_path = handle.name

        try:
            webbrowser.open(Path(temp_path).resolve().as_uri())
            messagebox.showinfo("Utskrift", "Utskriftsvinduet er åpnet. Velg skriver og trykk Skriv ut.")
        except OSError as error:
            messagebox.showerror("Utskriftsfeil", f"Kunne ikke åpne utskriftsvindu: {error}")


def main() -> None:
    root = tk.Tk()
    RecipeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
