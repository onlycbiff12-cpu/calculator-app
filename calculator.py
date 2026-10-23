# -*- coding: utf-8 -*-
"""آلة حاسبة مكتبية بواجهة رسومية — مكتبة tkinter المدمجة فقط.

التشغيل:
    python calculator.py

المحتوى:
    1) محرّك حساب آمن (ast) — بدون eval().
    2) واجهة رسومية: شاشة عرض + أزرار 0-9 والعمليات = C.
    3) معالجة الأخطاء: تظهر كلمة Error على الشاشة.
"""

from __future__ import annotations

import ast
import math
import sys
import tkinter as tk

# ==========================================================================
# 1) محرّك الحساب
# ==========================================================================

MAX_INPUT_LEN = 60      # أقصى طول للتعبير
MAX_EXPONENT = 400      # حدّ الأس لتجنّب الأرقام الضخمة
MAX_DIGITS = 100        # أقصى عدد خانات للناتج الصحيح

# رموز تُعرض على الشاشة وتُحوَّل إلى صيغة بايثون عند الحساب
DISPLAY_TO_CODE = {"×": "*", "÷": "/", "−": "-", "٫": "."}

_BIN_OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
}


class CalcError(Exception):
    """خطأ في التعبير الحسابي — يُترجم إلى رسالة Error على الشاشة."""


def to_code(text: str) -> str:
    """تحويل ما يظهر على الشاشة إلى تعبير بايثون."""
    for shown, code in DISPLAY_TO_CODE.items():
        text = text.replace(shown, code)
    return text.strip()


def _eval_node(node: ast.AST):
    """تقييم عقدة واحدة من شجرة التعبير، مع رفض أي شيء غير حسابي."""
    if isinstance(node, ast.Constant):
        value = node.value
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise CalcError("قيمة غير مدعومة")
        return value

    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Pow):
            if abs(right) > MAX_EXPONENT:
                raise CalcError("الأس كبير جدًا")
            return left ** right
        handler = _BIN_OPS.get(type(node.op))
        if handler is None:
            raise CalcError("عملية غير مدعومة")
        return handler(left, right)

    if isinstance(node, ast.UnaryOp):
        value = _eval_node(node.operand)
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.UAdd):
            return +value
        raise CalcError("عملية غير مدعومة")

    raise CalcError("تعبير غير صالح")


def evaluate(expression: str):
    """حساب تعبير وإرجاع الناتج، أو رفع CalcError عند أي خطأ."""
    text = to_code(expression)
    if not text:
        raise CalcError("لا يوجد تعبير")
    if len(text) > MAX_INPUT_LEN:
        raise CalcError("الإدخال طويل جدًا")

    try:
        tree = ast.parse(text, mode="eval")
    except (SyntaxError, ValueError):
        raise CalcError("تعبير غير مكتمل") from None

    try:
        value = _eval_node(tree.body)
    except ZeroDivisionError:
        raise CalcError("قسمة على صفر") from None
    except OverflowError:
        raise CalcError("الناتج كبير جدًا") from None
    except RecursionError:
        raise CalcError("تعبير متشعّب جدًا") from None

    if isinstance(value, float) and not math.isfinite(value):
        raise CalcError("الناتج غير معرّف")
    if isinstance(value, int) and len(str(abs(value))) > MAX_DIGITS:
        raise CalcError("الناتج كبير جدًا")
    return value


def format_result(value) -> str:
    """عرض الناتج بشكل مختصر وواضح."""
    if isinstance(value, int):
        return str(value)
    if value.is_integer() and abs(value) < 1e16:
        return str(int(value))
    return "{:.12g}".format(value)


# ==========================================================================
# 2) الواجهة الرسومية
# ==========================================================================

def _enable_dpi_awareness() -> None:
    """نص واضح على الشاشات عالية الدقة (Windows فقط، اختياري)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class Calculator(tk.Tk):
    """نافذة الآلة الحاسبة: شاشة عرض في الأعلى ولوحة أزرار أسفلها."""

    # ---- الألوان ----
    BG = "#101318"
    PANEL = "#171b23"
    BORDER = "#242c39"
    TEXT = "#eef2f8"
    MUTED = "#7d8798"
    ERROR = "#ff7b8a"

    NUM_BG, NUM_HOVER = "#1e232d", "#2a3140"
    OP_BG, OP_HOVER = "#233145", "#2e415c"
    OP_FG = "#7fb2ff"
    FN_BG, FN_HOVER = "#1a202b", "#232b38"
    FN_FG = "#c3cede"
    EQ_BG, EQ_HOVER = "#3b82f6", "#5b96f8"

    # ---- الأزرار: (النص، ما يُنفَّذ، النوع) ----
    KEYS = [
        ("C", "clear", "clear"), ("⌫", "back", "fn"),
        ("±", "negate", "fn"), ("÷", "÷", "op"),
        ("7", "7", "num"), ("8", "8", "num"), ("9", "9", "num"), ("×", "×", "op"),
        ("4", "4", "num"), ("5", "5", "num"), ("6", "6", "num"), ("−", "−", "op"),
        ("1", "1", "num"), ("2", "2", "num"), ("3", "3", "num"), ("+", "+", "op"),
        ("0", "0", "num"), (".", ".", "num"), ("=", "equals", "eq"),
    ]

    OPERATORS = "×÷−+"
    KEY_OPERATORS = {"*": "×", "/": "÷", "-": "−", "x": "×", "X": "×"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title("آلة حاسبة")
        self.geometry("360x560")
        self.minsize(300, 470)
        self.configure(bg=self.BG)

        self.expression = ""       # ما يُكتب حاليًا
        self.mode = "input"        # input | result | error
        self.last_line = ""        # سطر «التعبير =» بعد الحساب
        self.failed_text = ""      # التعبير الذي سبّب الخطأ
        self._value_size = 34
        self.buttons: dict[str, tk.Button] = {}

        self._build_display()
        self._build_keypad()
        self.bind("<Key>", self._on_key)
        self._refresh()

    # ---------------- الشاشة ----------------

    def _build_display(self) -> None:
        shell = tk.Frame(self, bg=self.PANEL, highlightbackground=self.BORDER,
                         highlightthickness=1)
        shell.pack(fill="x", padx=12, pady=(12, 10))

        self.history_var = tk.StringVar(value="")
        self.value_var = tk.StringVar(value="0")

        self.history_label = tk.Label(
            shell, textvariable=self.history_var, bg=self.PANEL, fg=self.MUTED,
            font=("Segoe UI", 11), anchor="e", justify="right")
        self.history_label.pack(fill="x", padx=12, pady=(10, 0))

        self.value_label = tk.Label(
            shell, textvariable=self.value_var, bg=self.PANEL, fg=self.TEXT,
            font=("Segoe UI Semibold", self._value_size), anchor="e",
            justify="right")
        self.value_label.pack(fill="x", padx=12, pady=(0, 10))

    # ---------------- الأزرار ----------------

    def _build_keypad(self) -> None:
        pad = tk.Frame(self, bg=self.BG)
        pad.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        for column in range(4):
            pad.columnconfigure(column, weight=1, uniform="key")
        for row in range(5):
            pad.rowconfigure(row, weight=1, uniform="row")

        for index, (label, action, kind) in enumerate(self.KEYS):
            row, column = divmod(index, 4)
            columnspan = 2 if label == "0" else 1
            button = self._make_button(pad, label, action, kind)
            button.grid(row=row, column=column, columnspan=columnspan,
                        sticky="nsew", padx=4, pady=4)
            self.buttons[label] = button

    def _make_button(self, parent, label, action, kind) -> tk.Button:
        bg, hover, fg = self._colors(kind)
        button = tk.Button(
            parent, text=label, command=self._command(action),
            bg=bg, fg=fg, activebackground=hover, activeforeground=fg,
            relief="flat", bd=0, highlightthickness=0, takefocus=0,
            cursor="hand2", font=("Segoe UI Semibold", 17))
        button.bind("<Enter>", lambda _e: button.configure(bg=hover))
        button.bind("<Leave>", lambda _e: button.configure(bg=bg))
        return button

    def _colors(self, kind: str):
        if kind == "num":
            return self.NUM_BG, self.NUM_HOVER, self.TEXT
        if kind == "op":
            return self.OP_BG, self.OP_HOVER, self.OP_FG
        if kind == "eq":
            return self.EQ_BG, self.EQ_HOVER, "#ffffff"
        if kind == "clear":
            return self.FN_BG, self.OP_HOVER, self.ERROR
        return self.FN_BG, self.FN_HOVER, self.FN_FG

    def _command(self, action: str):
        if action == "clear":
            return self._clear
        if action == "back":
            return self._backspace
        if action == "negate":
            return self._negate
        if action == "equals":
            return self._equals
        return lambda: self._insert(action)

    # ---------------- المنطق ----------------

    def _current_number(self) -> str:
        """الرقم الذي يُكتب الآن (بعد آخر عملية) لفحص الفاصلة العشرية."""
        index = len(self.expression)
        while index > 0 and (self.expression[index - 1].isdigit()
                             or self.expression[index - 1] == "."):
            index -= 1
        return self.expression[index:]

    def _insert(self, text: str) -> None:
        if self.mode == "error":       # أي إدخال جديد يبدأ من الصفر
            self._clear()

        if self.mode == "result":
            continues = text in self.OPERATORS
            self.expression = self.expression + text if continues else text
            self.mode = "input"
            self._refresh()
            return

        if text == ".":
            if "." in self._current_number():
                return
            if not self.expression or self.expression[-1] in self.OPERATORS:
                text = "0."
            self.expression += text
            self._refresh()
            return

        if text in self.OPERATORS:
            if not self.expression:
                return                  # لا يمكن البدء بعملية (السالب عبر ±)
            if self.expression[-1] in self.OPERATORS:
                self.expression = self.expression[:-1] + text   # استبدال العملية
            else:
                self.expression += text
            self._refresh()
            return

        self.expression += text
        self._refresh()

    def _clear(self) -> None:
        self.expression = ""
        self.last_line = ""
        self.failed_text = ""
        self.mode = "input"
        self._refresh()

    def _backspace(self) -> None:
        if self.mode in {"result", "error"}:
            self._clear()
            return
        self.expression = self.expression[:-1]
        self._refresh()

    def _negate(self) -> None:
        if self.mode == "error" or not self.expression:
            return
        if self.mode == "result":
            try:
                value = evaluate(self.expression)
            except CalcError:
                return
            self.expression = format_result(-value)
            self.last_line = ""
            self._refresh()
            return
        self.expression = self._negate_text(self.expression)
        if not self.expression:
            self.expression = "−"
        self._refresh()

    @staticmethod
    def _negate_text(text: str) -> str:
        if text.startswith("−(") and text.endswith(")"):
            return text[2:-1]
        if text.startswith("−"):
            return text[1:]
        return "−(" + text + ")"

    def _equals(self) -> None:
        text = self.expression
        if not text:
            return
        try:
            value = evaluate(text)
        except CalcError:
            self.mode = "error"
            self.failed_text = text
            self.last_line = ""
            self._refresh()
            return

        self.last_line = text + " ="
        self.expression = format_result(value)
        self.mode = "result"
        self._refresh()

    # ---------------- العرض ----------------

    @staticmethod
    def _pretty(text: str) -> str:
        """عرض إشارة السالب برمز موحّد على الشاشة."""
        return text.replace("-", "−")

    @staticmethod
    def _fit(text: str, limit: int) -> str:
        return text if len(text) <= limit else "…" + text[-limit:]

    def _refresh(self) -> None:
        if self.mode == "error":
            self.value_var.set("Error")
            self.value_label.configure(fg=self.ERROR)
            self.history_var.set(self._fit(self._pretty(self.failed_text), 34))
            self._resize_value_font("Error")
            return

        shown = self._pretty(self.expression) if self.expression else "0"
        self.value_var.set(self._fit(shown, 22))
        self.value_label.configure(fg=self.TEXT)
        self._resize_value_font(self._fit(shown, 22))

        if self.mode == "result":
            self.history_var.set(self._fit(self._pretty(self.last_line), 40))
        else:
            self.history_var.set("")

    def _resize_value_font(self, text: str) -> None:
        length = len(text)
        size = 34 if length <= 10 else (26 if length <= 15 else 20)
        if size != self._value_size:
            self._value_size = size
            self.value_label.configure(font=("Segoe UI Semibold", size))

    # ---------------- لوحة المفاتيح ----------------

    def _on_key(self, event):
        keysym = event.keysym
        if keysym in {"Return", "KP_Enter"}:
            self._equals()
            return "break"
        if keysym == "Escape":
            self._clear()
            return "break"
        if keysym == "BackSpace":
            self._backspace()
            return "break"
        if keysym == "Delete":
            self._clear()
            return "break"

        char = event.char
        if char == "=":
            self._equals()
            return "break"
        if char in self.KEY_OPERATORS:
            self._insert(self.KEY_OPERATORS[char])
            return "break"
        if char in "0123456789.+()":
            self._insert(char)
            return "break"
        return None


# ==========================================================================
# 3) نقطة الدخول
# ==========================================================================

def main() -> None:
    _enable_dpi_awareness()
    app = Calculator()
    app.mainloop()


if __name__ == "__main__":
    main()
