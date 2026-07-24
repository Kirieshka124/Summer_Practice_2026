import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from core import process_playlist


class MusicRecommenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Recommendation App")
        self.root.geometry("800x650")
        self.root.minsize(700, 550)

        self.bg_color = "#1e1e2e"
        self.fg_color = "#cdd6f4"
        self.accent_color = "#89b4fa"
        self.success_color = "#a6e3a1"
        self.error_color = "#f38ba8"

        self.root.configure(bg=self.bg_color)

        self.playlist_path = None
        self.result_data = None
        self.output_file = None

        self.create_widgets()

    def create_widgets(self):
        title = tk.Label(
            self.root,
            text="Music Recommendation App",
            font=("Segoe UI", 20, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        )
        title.pack(pady=15)

        file_frame = tk.Frame(self.root, bg=self.bg_color)
        file_frame.pack(fill="x", padx=20, pady=10)

        self.file_label = tk.Label(
            file_frame,
            text="Файл не выбран",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 10)
        )
        self.file_label.pack(side="left", padx=5)

        btn_select = tk.Button(
            file_frame,
            text="Выбрать плейлист",
            command=self.select_file,
            bg=self.accent_color,
            fg="#1e1e2e",
            font=("Segoe UI", 10),
            relief="flat",
            padx=10,
            pady=5
        )
        btn_select.pack(side="right")

        settings_frame = tk.Frame(self.root, bg=self.bg_color)
        settings_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(
            settings_frame,
            text="Количество рекомендаций:",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 10)
        ).pack(side="left", padx=5)

        # Поле ввода без значения по умолчанию
        self.top_n_var = tk.StringVar(value="")
        top_n_entry = tk.Entry(
            settings_frame,
            textvariable=self.top_n_var,
            width=5,
            bg="#313244",
            fg=self.fg_color,
            font=("Segoe UI", 10),
            relief="flat"
        )
        top_n_entry.pack(side="left", padx=5)
        # Добавляем подсказку
        top_n_entry.insert(0, "25")
        top_n_entry.bind("<FocusIn>", lambda e: top_n_entry.delete(0, tk.END) if top_n_entry.get() == "25" else None)

        self.btn_run = tk.Button(
            self.root,
            text="Запустить обработку",
            command=self.run_processing,
            bg=self.success_color,
            fg="#1e1e2e",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            padx=20,
            pady=10
        )
        self.btn_run.pack(pady=10)

        self.progress = ttk.Progressbar(
            self.root,
            mode="indeterminate",
            length=400
        )
        self.progress.pack(pady=5)

        self.status_label = tk.Label(
            self.root,
            text="Готов к работе",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 10)
        )
        self.status_label.pack(pady=5)

        separator = tk.Frame(self.root, height=2, bg="#313244")
        separator.pack(fill="x", padx=20, pady=5)

        log_frame = tk.Frame(self.root, bg=self.bg_color)
        log_frame.pack(fill="both", expand=True, padx=20, pady=5)

        tk.Label(
            log_frame,
            text="Вывод программы:",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")

        self.log_text = tk.Text(
            log_frame,
            height=15,
            bg="#0d1117",
            fg="#c9d1d9",
            font=("Consolas", 10),
            relief="flat",
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, pady=5)

        scrollbar = tk.Scrollbar(self.log_text)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)

        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(fill="x", padx=20, pady=5)

        self.btn_save = tk.Button(
            btn_frame,
            text="Сохранить результат",
            command=self.save_result,
            bg=self.accent_color,
            fg="#1e1e2e",
            font=("Segoe UI", 10),
            relief="flat",
            padx=10,
            pady=5,
            state="disabled"
        )
        self.btn_save.pack(side="left", padx=5)

        self.btn_open_folder = tk.Button(
            btn_frame,
            text="Открыть папку",
            command=self.open_output_folder,
            bg="#313244",
            fg=self.fg_color,
            font=("Segoe UI", 10),
            relief="flat",
            padx=10,
            pady=5
        )
        self.btn_open_folder.pack(side="left", padx=5)

        self.btn_clear_log = tk.Button(
            btn_frame,
            text="Очистить вывод",
            command=self.clear_log,
            bg="#313244",
            fg=self.fg_color,
            font=("Segoe UI", 10),
            relief="flat",
            padx=10,
            pady=5
        )
        self.btn_clear_log.pack(side="left", padx=5)

    def log(self, message: str):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def log_error(self, message: str):
        self.log_text.insert(tk.END, "ОШИБКА: " + message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        self.log_text.delete("1.0", tk.END)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Выберите плейлист",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if not file_path:
            return

        source = Path(file_path)
        self.playlist_path = source
        self.file_label.config(text=f"Файл: {source.name}")
        self.log(f"Выбран файл: {source.name}")

    def run_processing(self):
        if not self.playlist_path:
            messagebox.showwarning("Предупреждение", "Сначала выберите файл с плейлистом")
            return

        if not self.playlist_path.exists():
            messagebox.showerror("Ошибка", "Файл не найден")
            return

        # Получаем количество рекомендаций
        top_n_str = self.top_n_var.get().strip()
        if not top_n_str or top_n_str == "25":
            top_n = 25
        else:
            try:
                top_n = int(top_n_str)
                if top_n < 1:
                    messagebox.showwarning("Предупреждение", "Количество рекомендаций должно быть больше 0")
                    return
            except ValueError:
                messagebox.showwarning("Предупреждение", "Введите число")
                return

        self.btn_run.config(state="disabled", text="Обработка...")
        self.progress.start(10)
        self.status_label.config(text="Идет обработка...")
        self.log("")
        self.log(" " * 60)
        self.log("Запуск обработки")
        self.log(" " * 60)

        thread = threading.Thread(target=self.process, args=(top_n,), daemon=True)
        thread.start()

    def process(self, top_n):
        try:
            self.log(f"Количество рекомендаций: {top_n}")
            self.log(f"Плейлист: {self.playlist_path.name}")
            self.log("")

            result = process_playlist(self.playlist_path, top_n, log_callback=self.log)

            if "error" in result:
                self.root.after(0, self.show_error, result["error"])
                return

            self.root.after(0, self.update_result, result)

        except Exception as e:
            self.root.after(0, self.show_error, str(e))

    def update_result(self, result):
        self.progress.stop()
        self.btn_run.config(state="normal", text="Запустить обработку")

        if "error" in result:
            self.status_label.config(text="Ошибка")
            self.log("")
            self.log_error(result["error"])
            return

        self.result_data = result
        self.output_file = result.get("output_file")

        stats = result.get("stats", {})
        self.status_label.config(
            text=f"Обработано: {stats.get('processed', 0)} из {stats.get('total', 0)} треков"
        )

        self.log("")
        self.log(" " * 60)
        self.log("СТАТИСТИКА ОБРАБОТКИ")
        self.log(" " * 60)
        self.log(f"  Всего треков: {stats.get('total', 0)}")
        self.log(f"  Успешно обработано: {stats.get('processed', 0)}")
        self.log(f"  Пропущено: {stats.get('skipped', 0)}")

        # Все теги, без ограничения
        tags = result.get("tags", [])
        if tags:
            self.log("")
            self.log(" " * 60)
            self.log("ВСЕ ТЕГИ")
            self.log(" " * 60)
            for tag, count in tags:
                self.log(f"  {tag}: {count}")
        else:
            self.log("Теги не найдены")

        recommendations = result.get("recommendations", [])
        if recommendations:
            self.log("")
            self.log(" " * 60)
            self.log("ТОП РЕКОМЕНДАЦИЙ")
            self.log(" " * 60)
            # Показываем все рекомендации
            for i, rec in enumerate(recommendations, 1):
                self.log(f"  {i:2}. {rec.artist} - {rec.name}  (score: {rec.score:.3f})")
        else:
            self.log("Рекомендаций не найдено")

        self.log("")
        self.log(" " * 60)
        self.log("Готово")
        self.log(" " * 60)

        if self.output_file:
            self.btn_save.config(state="normal")
            self.log(f"Результат сохранен в: output/{self.output_file}")

    def show_error(self, error_msg):
        self.progress.stop()
        self.btn_run.config(state="normal", text="Запустить обработку")
        self.status_label.config(text="Ошибка")
        self.log("")
        self.log_error(error_msg)
        messagebox.showerror("Ошибка", error_msg)

    def save_result(self):
        if not self.output_file:
            messagebox.showwarning("Предупреждение", "Нет результатов для сохранения")
            return

        file_path = Path("output") / self.output_file
        if not file_path.exists():
            messagebox.showerror("Ошибка", "Файл с результатами не найден")
            return

        save_path = filedialog.asksaveasfilename(
            title="Сохранить результат",
            defaultextension=".txt",
            initialfile=self.output_file,
            filetypes=[("Текстовые файлы", "*.txt")]
        )

        if save_path:
            try:
                shutil.copy(file_path, save_path)
                self.log(f"Файл сохранен: {save_path}")
                messagebox.showinfo("Успех", f"Файл сохранен:\n{save_path}")
            except Exception as e:
                error_msg = f"Ошибка при сохранении: {e}"
                self.log_error(error_msg)
                messagebox.showerror("Ошибка", error_msg)

    def open_output_folder(self):
        import os
        output_dir = Path("output")
        if output_dir.exists():
            os.startfile(str(output_dir))
        else:
            messagebox.showinfo("Информация", "Папка output не существует")


if __name__ == "__main__":
    root = tk.Tk()
    app = MusicRecommenderGUI(root)
    root.mainloop()