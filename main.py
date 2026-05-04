import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import random
import json
import os
from datetime import datetime
from collections import defaultdict

# ==================== ДАННЫЕ ====================
DEFAULT_QUOTES = [
    {"text": "Будь изменением, которое ты хочешь видеть в мире.", "author": "Махатма Ганди", "theme": "Мотивация"},
    {"text": "Жизнь — это то, что с тобой происходит, пока ты строишь другие планы.", "author": "Джон Леннон",
     "theme": "Жизнь"},
    {"text": "Единственный способ делать великую работу — любить то, что ты делаешь.", "author": "Стив Джобс",
     "theme": "Работа"},
    {"text": "Ты не можешь использовать старую карту, чтобы открыть новую страну.", "author": "Марк Твен",
     "theme": "Развитие"},
    {"text": "Воображение важнее знания.", "author": "Альберт Эйнштейн", "theme": "Наука"},
    {"text": "То, что тебя не убивает, делает тебя сильнее.", "author": "Фридрих Ницше", "theme": "Философия"},
    {"text": "Сложись или умри, пытаясь.", "author": "Тайлер Дёрден", "theme": "Мотивация"},
    {"text": "Успех — это способность идти от неудачи к неудаче, не теряя энтузиазма.", "author": "Уинстон Черчилль",
     "theme": "Успех"},
]

HISTORY_FILE = "quotes_history.json"


class QuoteGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("🌸 Random Quote Generator 🌸")
        self.root.geometry("750x650")
        self.root.configure(bg="#FFE4EC")  # Светло-розовый фон

        # Данные
        self.quotes = DEFAULT_QUOTES.copy()
        self.history = []  # Каждая запись: {"text":..., "author":..., "theme":..., "timestamp":...}

        # Загружаем историю
        self.load_history()

        # Строим интерфейс
        self.create_widgets()
        self.update_stats()
        self.update_filter_options()
        self.refresh_history_display()

    # ========== РОЗОВЫЙ ИНТЕРФЕЙС ==========
    def create_widgets(self):
        # Стиль
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Pink.TButton", background="#FFB6C1", foreground="#B0306E", font=("Helvetica", 10, "bold"))
        style.map("Pink.TButton", background=[("active", "#FF69B4")])

        # Заголовок
        title = tk.Label(self.root, text="✨ Генератор случайных цитат ✨", font=("Helvetica", 20, "bold"), bg="#FFE4EC",
                         fg="#C71585")
        title.pack(pady=15)

        # === Панель генерации ===
        frame_gen = tk.Frame(self.root, bg="#FFE4EC")
        frame_gen.pack(pady=10)

        self.generate_btn = tk.Button(frame_gen, text="🎲 Сгенерировать цитату 🎲", command=self.generate_random_quote,
                                      bg="#FF69B4", fg="white", font=("Helvetica", 12, "bold"), padx=20, pady=10,
                                      relief="raised", bd=3, activebackground="#FF1493")
        self.generate_btn.pack()

        # === Блок отображения текущей цитаты ===
        frame_display = tk.LabelFrame(self.root, text="📖 Текущая цитата", font=("Helvetica", 12, "bold"),
                                      bg="#FFE4EC", fg="#B0306E", bd=2, relief="groove")
        frame_display.pack(fill="both", expand=False, padx=20, pady=10)

        self.quote_text = tk.Text(frame_display, height=4, wrap=tk.WORD, font=("Georgia", 12), bg="#FFF0F5",
                                  fg="#8B0045",
                                  relief="sunken", bd=2)
        self.quote_text.pack(fill="both", padx=10, pady=10)
        self.quote_text.insert(tk.END, "Нажми кнопку, чтобы получить вдохновение...")

        # === Фильтры ===
        frame_filters = tk.LabelFrame(self.root, text="🔍 Фильтры истории", font=("Helvetica", 11, "bold"),
                                      bg="#FFE4EC", fg="#B0306E", bd=2, relief="groove")
        frame_filters.pack(fill="x", padx=20, pady=5)

        # Фильтр по автору
        tk.Label(frame_filters, text="Автор:", bg="#FFE4EC", fg="#B0306E", font=("Helvetica", 10)).grid(row=0, column=0,
                                                                                                        padx=5, pady=5,
                                                                                                        sticky="e")
        self.author_filter_var = tk.StringVar(value="Все")
        self.author_combo = ttk.Combobox(frame_filters, textvariable=self.author_filter_var, state="readonly", width=20)
        self.author_combo.grid(row=0, column=1, padx=5, pady=5)
        self.author_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_history_display())

        # Фильтр по теме
        tk.Label(frame_filters, text="Тема:", bg="#FFE4EC", fg="#B0306E", font=("Helvetica", 10)).grid(row=0, column=2,
                                                                                                       padx=5, pady=5,
                                                                                                       sticky="e")
        self.theme_filter_var = tk.StringVar(value="Все")
        self.theme_combo = ttk.Combobox(frame_filters, textvariable=self.theme_filter_var, state="readonly", width=20)
        self.theme_combo.grid(row=0, column=3, padx=5, pady=5)
        self.theme_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_history_display())

        tk.Button(frame_filters, text="Сбросить фильтры", command=self.reset_filters,
                  bg="#FFB6C1", fg="#B0306E", font=("Helvetica", 9)).grid(row=0, column=4, padx=10, pady=5)

        # Статистика
        self.stats_label = tk.Label(frame_filters, text="", bg="#FFE4EC", fg="#C71585", font=("Helvetica", 9, "italic"))
        self.stats_label.grid(row=1, column=0, columnspan=5, pady=2)

        # === Блок истории ===
        frame_history = tk.LabelFrame(self.root, text="📜 История цитат", font=("Helvetica", 11, "bold"),
                                      bg="#FFE4EC", fg="#B0306E", bd=2, relief="groove")
        frame_history.pack(fill="both", expand=True, padx=20, pady=10)

        # Список истории
        scrollbar = tk.Scrollbar(frame_history)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_listbox = tk.Listbox(frame_history, yscrollcommand=scrollbar.set, font=("Helvetica", 10),
                                          bg="#FFF0F5", fg="#8B0045", selectbackground="#FFB6C1", height=12)
        self.history_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        scrollbar.config(command=self.history_listbox.yview)

        # Кнопка очистки истории
        btn_clear = tk.Button(self.root, text="🧹 Очистить историю", command=self.clear_history,
                              bg="#FFA07A", fg="white", font=("Helvetica", 10), padx=10)
        btn_clear.pack(pady=5)

        # === Добавление новой цитаты ===
        frame_add = tk.LabelFrame(self.root, text="➕ Добавить свою цитату", font=("Helvetica", 10, "bold"),
                                  bg="#FFE4EC", fg="#B0306E", bd=2, relief="groove")
        frame_add.pack(fill="x", padx=20, pady=5)

        tk.Label(frame_add, text="Текст:", bg="#FFE4EC", fg="#B0306E").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.new_text_entry = tk.Entry(frame_add, width=50, bg="white")
        self.new_text_entry.grid(row=0, column=1, padx=5, pady=5, columnspan=2)

        tk.Label(frame_add, text="Автор:", bg="#FFE4EC", fg="#B0306E").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.new_author_entry = tk.Entry(frame_add, width=20, bg="white")
        self.new_author_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        tk.Label(frame_add, text="Тема:", bg="#FFE4EC", fg="#B0306E").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.new_theme_entry = tk.Entry(frame_add, width=20, bg="white")
        self.new_theme_entry.grid(row=1, column=3, padx=5, pady=5)

        tk.Button(frame_add, text="💾 Добавить цитату", command=self.add_quote,
                  bg="#FFB6C1", fg="#8B0045", font=("Helvetica", 9, "bold")).grid(row=2, column=0, columnspan=4, pady=5)

    # ========== ЛОГИКА ==========
    def generate_random_quote(self):
        if not self.quotes:
            messagebox.showwarning("Нет цитат", "Список цитат пуст! Добавьте хотя бы одну.")
            return

        quote = random.choice(self.quotes)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Сохраняем в историю
        entry = {
            "text": quote["text"],
            "author": quote["author"],
            "theme": quote["theme"],
            "timestamp": timestamp
        }
        self.history.append(entry)
        self.save_history()

        # Отображаем
        self.quote_text.delete(1.0, tk.END)
        self.quote_text.insert(tk.END,
                               f"«{quote['text']}»\n\n— {quote['author']}\n📂 Тема: {quote['theme']}\n🕒 {timestamp}")

        self.update_stats()
        self.update_filter_options()
        self.refresh_history_display()

    def refresh_history_display(self):
        """Показывает историю с учётом фильтров"""
        self.history_listbox.delete(0, tk.END)

        author_filter = self.author_filter_var.get()
        theme_filter = self.theme_filter_var.get()

        filtered = self.history
        if author_filter != "Все":
            filtered = [h for h in filtered if h["author"] == author_filter]
        if theme_filter != "Все":
            filtered = [h for h in filtered if h["theme"] == theme_filter]

        if not filtered:
            self.history_listbox.insert(tk.END, "Нет цитат с такими фильтрами")
            return

        for entry in filtered:
            display = f"{entry['timestamp']} | {entry['author']} — {entry['text'][:60]}..."
            self.history_listbox.insert(tk.END, display)

    def update_filter_options(self):
        """Обновляет выпадающие списки авторов и тем"""
        authors = sorted(set(q["author"] for q in self.quotes))
        themes = sorted(set(q["theme"] for q in self.quotes))

        self.author_combo['values'] = ["Все"] + authors
        self.theme_combo['values'] = ["Все"] + themes

        # Если текущее значение невалидно — сбросить
        if self.author_filter_var.get() not in self.author_combo['values']:
            self.author_filter_var.set("Все")
        if self.theme_filter_var.get() not in self.theme_combo['values']:
            self.theme_filter_var.set("Все")

    def update_stats(self):
        total = len(self.history)
        self.stats_label.config(text=f"📊 Всего сгенерировано цитат: {total}")

    def reset_filters(self):
        self.author_filter_var.set("Все")
        self.theme_filter_var.set("Все")
        self.refresh_history_display()

    def add_quote(self):
        text = self.new_text_entry.get().strip()
        author = self.new_author_entry.get().strip()
        theme = self.new_theme_entry.get().strip()

        # Проверка на пустые строки
        if not text:
            messagebox.showerror("Ошибка", "Текст цитаты не может быть пустым!")
            return
        if not author:
            messagebox.showerror("Ошибка", "Автор не может быть пустым!")
            return
        if not theme:
            messagebox.showerror("Ошибка", "Тема не может быть пустой!")
            return

        new_quote = {"text": text, "author": author, "theme": theme}
        self.quotes.append(new_quote)

        # Очищаем поля
        self.new_text_entry.delete(0, tk.END)
        self.new_author_entry.delete(0, tk.END)
        self.new_theme_entry.delete(0, tk.END)

        self.update_filter_options()
        messagebox.showinfo("Успех", f"Цитата от {author} добавлена!")

    def clear_history(self):
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить всю историю?"):
            self.history = []
            self.save_history()
            self.update_stats()
            self.refresh_history_display()
            self.quote_text.delete(1.0, tk.END)
            self.quote_text.insert(tk.END, "Нажми кнопку, чтобы получить вдохновение...")

    # ========== РАБОТА С ФАЙЛАМИ ==========
    def save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except:
                self.history = []
        else:
            self.history = []


# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = QuoteGenerator(root)
    root.mainloop()