"""
Nova Calculator
A modern, resizable desktop calculator built with Python's Tkinter (standard library).

Run:
    python nova_calculator.py

Features:
- Standard arithmetic, %, reciprocal, square, square root, sign toggle
- Keyboard input (0-9, +, -, *, /, Enter, Backspace, Escape)
- Expand / compact layout toggle
- Native window minimize, maximize, resize, and close controls
- Newest-first calculation history (stack behavior), with click-to-reuse
"""

import ast
import math
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path


BG = "#171a20"
PANEL = "#1d2129"
BUTTON = "#2b3039"
BUTTON_HOVER = "#373e49"
OPERATOR = "#303641"
ACCENT = "#20dce5"
TEXT = "#f4f7fb"
MUTED = "#9ba5b4"
ERROR = "#ff7b85"

def resource_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = Path(__file__).resolve().parent
    
    return Path(base_path) / filename


class SafeMath:
    """Evaluate only numeric constants and explicitly allowed arithmetic AST nodes."""

    OPS = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.Pow: lambda a, b: a ** b,
        ast.Mod: lambda a, b: a % b,
    }
    UNARY = {
        ast.UAdd: lambda a: a,
        ast.USub: lambda a: -a,
    }

    @classmethod
    def evaluate(cls, expression):
        tree = ast.parse(expression, mode="eval")
        return cls._node(tree.body)

    @classmethod
    def _node(cls, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in cls.OPS:
            left, right = cls._node(node.left), cls._node(node.right)
            result = cls.OPS[type(node.op)](left, right)
            if isinstance(result, complex):
                raise ValueError("Complex results are not supported")
            return result
        if isinstance(node, ast.UnaryOp) and type(node.op) in cls.UNARY:
            return cls.UNARY[type(node.op)](cls._node(node.operand))
        raise ValueError("Unsupported expression")


class NovaCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Nova Calculator")
        self.root.geometry("430x650")
        self.root.minsize(330, 460)
        self.root.configure(bg=BG)
        #application icon
        self.app_icon = tk.PhotoImage(
            file = str(resource_path("calculator.png"))
        )
        self.root.iconphoto(True, self.app_icon)

        self.expression = ""
        self.just_evaluated = False
        self.history = []  # newest item at index 0: stack-like history
        self.compact = False
        self.history_visible = False

        self.display_var = tk.StringVar(value="0")
        self.preview_var = tk.StringVar(value="")
        self._build()
        self._bind_keys()
        self._apply_layout()

    def _build(self):
        self.top = tk.Frame(self.root, bg=BG)
        self.top.pack(fill="x", padx=16, pady=(12, 4))

        self.mode_label = tk.Label(
            self.top, text="STANDARD", bg=BG, fg=TEXT,
            font=("Segoe UI Semibold", 11)
        )
        self.mode_label.pack(side="left")

        self.compact_btn = self._make_button(
            self.top, "⇲", self.toggle_compact, width=3, height=1,
            bg=BG, fg=MUTED, font=("Segoe UI", 13)
        )
        self.compact_btn.pack(side="left", padx=(12, 0))

        self.history_btn = self._make_button(
            self.top, "History", self.toggle_history, width=8, height=1,
            bg=BG, fg=MUTED, font=("Segoe UI", 10)
        )
        self.history_btn.pack(side="right")

        self.display_frame = tk.Frame(self.root, bg=BG)
        self.display_frame.pack(fill="both", expand=True, padx=18, pady=(8, 6))

        self.preview = tk.Label(
            self.display_frame, textvariable=self.preview_var, anchor="e",
            bg=BG, fg=MUTED, font=("Segoe UI", 12)
        )
        self.preview.pack(fill="x", pady=(10, 0))

        self.display = tk.Label(
            self.display_frame, textvariable=self.display_var, anchor="e",
            bg=BG, fg=TEXT, font=("Segoe UI Light", 42), padx=2
        )
        self.display.pack(fill="x", expand=True, anchor="se")

        self.memory = tk.Frame(self.root, bg=BG)
        for label in ("MC", "MR", "M+", "M−", "MS"):
            b = self._make_button(
                self.memory, label, lambda x=label: self.memory_action(x),
                bg=BG, fg=MUTED, font=("Segoe UI", 9), height=1
            )
            b.pack(side="left", expand=True, fill="x")

        self.keypad = tk.Frame(self.root, bg=BG)
        self.keypad.pack(fill="x", padx=4, pady=(4, 5))

        self.keys = [
            [("%", "percent"), ("CE", "clear_entry"), ("C", "clear"), ("⌫", "backspace")],
            [("1/x", "reciprocal"), ("x²", "square"), ("√x", "sqrt"), ("÷", "/")],
            [("7", "7"), ("8", "8"), ("9", "9"), ("×", "*")],
            [("4", "4"), ("5", "5"), ("6", "6"), ("−", "-")],
            [("1", "1"), ("2", "2"), ("3", "3"), ("+", "+")],
            [("+/−", "sign"), ("0", "0"), (".", "."), ("=", "equals")],
        ]
        self.key_buttons = []
        for r, row in enumerate(self.keys):
            row_buttons = []
            for c, (label, action) in enumerate(row):
                is_equal = action == "equals"
                is_operator = action in {"+", "-", "*", "/", "equals"}
                color = ACCENT if is_equal else (OPERATOR if is_operator else BUTTON)
                fg = "#08252a" if is_equal else TEXT
                btn = self._make_button(
                    self.keypad, label,
                    lambda a=action: self.handle(a),
                    bg=color, fg=fg, font=("Segoe UI", 14),
                    height=2
                )
                btn.grid(row=r, column=c, sticky="nsew", padx=2, pady=2, ipady=8)
                row_buttons.append(btn)
            self.keypad.grid_rowconfigure(r, weight=1)
            self.key_buttons.append(row_buttons)
        for c in range(4):
            self.keypad.grid_columnconfigure(c, weight=1, uniform="keys")

        self.history_panel = tk.Frame(self.root, bg=PANEL, width=210)
        self.history_title = tk.Label(
            self.history_panel, text="Recent calculations",
            bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 11), anchor="w"
        )
        self.history_title.pack(fill="x", padx=12, pady=(14, 8))
        self.history_list = tk.Listbox(
            self.history_panel, bg=PANEL, fg=TEXT, selectbackground="#394552",
            selectforeground=TEXT, borderwidth=0, highlightthickness=0,
            font=("Segoe UI", 10), activestyle="none"
        )
        self.history_list.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.history_list.bind("<Double-Button-1>", self.use_history_item)
        self.clear_history_btn = self._make_button(
            self.history_panel, "Clear history", self.clear_history,
            bg=BUTTON, fg=TEXT, font=("Segoe UI", 10), height=1
        )
        self.clear_history_btn.pack(fill="x", padx=10, pady=(0, 12))

    def _make_button(self, parent, text, command, **style):
        bg = style.pop("bg", BUTTON)
        fg = style.pop("fg", TEXT)
        font = style.pop("font", ("Segoe UI", 12))
        height = style.pop("height", 2)
        width = style.pop("width", None)
        button = tk.Button(
            parent, text=text, command=command, bg=bg, fg=fg,
            activebackground=ACCENT if text == "=" else BUTTON_HOVER,
            activeforeground="#08252a" if text == "=" else TEXT,
            relief="flat", bd=0, cursor="hand2", font=font,
            height=height, width=width, highlightthickness=0
        )
        if bg not in (BG, ACCENT):
            button.bind("<Enter>", lambda _e, b=button: b.configure(bg=BUTTON_HOVER))
            button.bind("<Leave>", lambda _e, b=button, color=bg: b.configure(bg=color))
        return button

    def _apply_layout(self):
        if self.compact:
            self.root.geometry("330x455")
            self.root.minsize(300, 420)
            self.mode_label.configure(text="COMPACT")
            self.memory.pack_forget()
            self.history_panel.pack_forget()
            self.preview.pack_forget()
            self.display.configure(font=("Segoe UI Light", 32))
            for row in self.key_buttons:
                for button in row:
                    button.configure(font=("Segoe UI", 12))
                    button.grid_configure(ipady=3)
        else:
            self.root.geometry("480x690")
            self.root.minsize(360, 500)
            self.mode_label.configure(text="STANDARD")
            self.preview.pack(fill="x", pady=(10, 0), before=self.display)
            self.memory.pack(fill="x", padx=10, pady=(0, 2), before=self.keypad)
            self.display.configure(font=("Segoe UI Light", 42))
            for row in self.key_buttons:
                for button in row:
                    button.configure(font=("Segoe UI", 14))
                    button.grid_configure(ipady=8)
            if self.history_visible:
                self.history_panel.pack(side="right", fill="y", padx=(0, 6), pady=8)
        self.compact_btn.configure(text="⇱" if self.compact else "⇲")

    def toggle_compact(self):
        self.compact = not self.compact
        self.history_visible = False
        self._apply_layout()

    def toggle_history(self):
        if self.compact:
            self.compact = False
            self._apply_layout()
        self.history_visible = not self.history_visible
        if self.history_visible:
            self.history_panel.pack(side="right", fill="y", padx=(0, 6), pady=8)
            self.history_btn.configure(fg=ACCENT)
        else:
            self.history_panel.pack_forget()
            self.history_btn.configure(fg=MUTED)

    def _format(self, value):
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError("Result is not finite")
            if value.is_integer() and abs(value) < 1e16:
                return str(int(value))
            return f"{value:.12g}"
        return str(value)

    def _set_value(self, value):
        self.display_var.set(value)
        self.display.configure(fg=TEXT)

    def _current_number(self):
        return float(self.display_var.get().replace(",", ""))

    def handle(self, action):
        if action in "0123456789" and len(action) == 1:
            if self.just_evaluated:
                self.expression = ""
                self._set_value("0")
                self.just_evaluated = False
            current = self.display_var.get()
            self._set_value(action if current == "0" else current + action)
            return

        if action == ".":
            if self.just_evaluated:
                self._set_value("0")
                self.just_evaluated = False
            if "." not in self.display_var.get():
                self._set_value(self.display_var.get() + ".")
            return

        if action in {"+", "-", "*", "/"}:
            self.expression += self.display_var.get() + action
            self.preview_var.set(self.expression.replace("*", "×").replace("/", "÷"))
            self._set_value("0")
            self.just_evaluated = False
            return

        try:
            value = self._current_number()
            if action == "equals":
                if self.expression:
                    full = self.expression + self.display_var.get()
                    result = SafeMath.evaluate(full)
                    formatted = self._format(result)
                    self._add_history(full, formatted)
                    self.preview_var.set(full.replace("*", "×").replace("/", "÷") + " =")
                    self._set_value(formatted)
                    self.expression = ""
                    self.just_evaluated = True
            elif action == "clear":
                self.expression = ""
                self.preview_var.set("")
                self._set_value("0")
                self.just_evaluated = False
            elif action == "clear_entry":
                self._set_value("0")
            elif action == "backspace":
                current = self.display_var.get()
                self._set_value(current[:-1] if len(current) > 1 else "0")
            elif action == "sign":
                self._set_value(self._format(-value))
            elif action == "percent":
                self._set_value(self._format(value / 100))
            elif action == "reciprocal":
                self._set_value(self._format(1 / value))
            elif action == "square":
                self._set_value(self._format(value ** 2))
            elif action == "sqrt":
                if value < 0:
                    raise ValueError("Cannot take the square root of a negative number")
                self._set_value(self._format(math.sqrt(value)))
        except ZeroDivisionError:
            self._show_error("Cannot divide by zero")
        except (ValueError, SyntaxError, OverflowError) as exc:
            self._show_error(str(exc) or "Invalid calculation")

    def _show_error(self, message):
        self._set_value("Error")
        self.display.configure(fg=ERROR)
        self.preview_var.set(message)
        self.expression = ""
        self.just_evaluated = True

    def _add_history(self, expression, result):
        self.history.insert(0, (expression, result))
        self.history_list.insert(0, f"{expression} = {result}")

    def use_history_item(self, _event=None):
        selection = self.history_list.curselection()
        if selection:
            _expression, result = self.history[selection[0]]
            self._set_value(result)
            self.expression = ""
            self.preview_var.set("")
            self.just_evaluated = True

    def clear_history(self):
        self.history.clear()
        self.history_list.delete(0, tk.END)

    def memory_action(self, action):
        # Memory keys are included in the interface; full memory registers can be added next.
        if action in {"MC", "MR", "M+", "M−", "MS"}:
            self.preview_var.set(f"{action} — memory register is a planned extension")

    def _bind_keys(self):
        self.root.bind("<Key>", self.on_key)
        self.root.bind("<Return>", lambda _e: self.handle("equals"))
        self.root.bind("<KP_Enter>", lambda _e: self.handle("equals"))
        self.root.bind("<BackSpace>", lambda _e: self.handle("backspace"))
        self.root.bind("<Escape>", lambda _e: self.handle("clear"))

    def on_key(self, event):
        char = event.char
        if char in "0123456789" and len(char) == 1:
            self.handle(char)
        elif char in "+-*/":
            self.handle(char)
        elif char == ".":
            self.handle(".")


if __name__ == "__main__":
    root = tk.Tk()
    app = NovaCalculator(root)
    root.mainloop()
