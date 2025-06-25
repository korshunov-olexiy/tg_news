import os
import functools

class Debugger:
    enabled = False  # За замовчуванням вимкнено
    @classmethod
    def set_enabled(cls, value: bool):
        cls.enabled = value

    @classmethod
    def print_vars(cls, **kwargs):
        if not cls.enabled:
            return
        print("[DEBUG] Variables:")
        for k, v in kwargs.items():
            print(f"    {k} = {v}")

    @classmethod
    def print_vars_to_log(cls, save_to_log, **kwargs):
        if not cls.enabled:
            return
        # Створюємо шлях до файлу, якщо потрібно
        dir_name = os.path.dirname(save_to_log)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        lines = ["[DEBUG] Variables:"]
        for k, v in kwargs.items():
            lines.append(f"    {k} = {v}")
        lines.append("")  # Порожній рядок для розділення записів
        with open(save_to_log, "a", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def __init__(self, *var_names):
        self.var_names = var_names

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if Debugger.enabled:
                print(f"[DEBUG] Calling {func.__name__}()")
                print(f"  args: {args}")
                print(f"  kwargs: {kwargs}")
            result = func(*args, **kwargs)
            if Debugger.enabled:
                for idx, var in enumerate(func.__code__.co_varnames):
                    if var in self.var_names and idx < len(args):
                        print(f"    {var} = {args[idx]}")
                for var in self.var_names:
                    if var in kwargs:
                        print(f"    {var} = {kwargs[var]}")
                print(f"[DEBUG] {func.__name__}() returned {result}")
            return result
        return wrapper
