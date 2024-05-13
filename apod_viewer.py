import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from datetime import date
import apod_desktop
import image_lib

script_dir = os.path.dirname(os.path.abspath(__file__))
default_image_path = os.path.join(script_dir, 'nasa.ico')


class APODViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("APOD Viewer")
        self.iconbitmap(default='nasa.ico')
        self.geometry("800x600")
        self.minsize(400, 300)

        self.create_widgets()
        self.load_default_image()

    def create_widgets(self):
        # Image display
        self.image_label = ttk.Label(self)
        self.image_label.grid(row=0, column=0, padx=10, pady=10)

        # Text description of the image
        self.explanation_text = tk.Text(self, wrap='word', height=10)
        self.explanation_text.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky='nsew')
        self.explanation_text.grid_remove()  # Hide by default

        # Frames for viewing cached image and getting more images
        self.view_cached_frame = ttk.Frame(self)
        self.view_cached_frame.grid(row=2, column=0, padx=10, pady=10, sticky='ew')

        self.get_more_frame = ttk.Frame(self)
        self.get_more_frame.grid(row=2, column=1, padx=10, pady=10, sticky='ew')

        # Inside "View Cached Image" frame
        ttk.Label(self.view_cached_frame, text="Select Image: ").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.image_var = tk.StringVar()
        self.image_dropdown = ttk.Combobox(self.view_cached_frame, textvariable=self.image_var, state='readonly')
        self.image_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.load_apod_list()

        # Bind event to update image display and explanation text
        self.image_dropdown.bind("<<ComboboxSelected>>", self.show_selected_apod)

        self.set_as_desktop_button = ttk.Button(self.view_cached_frame, text="Set as Desktop",
                                                command=self.set_desktop_background)
        self.set_as_desktop_button.grid(row=0, column=2, padx=5, pady=5, sticky='w')
        # self.set_as_desktop_button.config(state="disabled")

        # Inside "Get More Images" frame
        ttk.Label(self.get_more_frame, text="Select Date: ").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.date_var = tk.StringVar()
        self.date_entry = ttk.Entry(self.get_more_frame, textvariable=self.date_var)
        self.date_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        self.download_button = ttk.Button(self.get_more_frame, text="Download Image", command=self.get_apod)
        self.download_button.grid(row=0, column=2, padx=5, pady=5, sticky='w')

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

    def load_default_image(self):
        self.display_image(default_image_path)

    def load_apod_list(self):
        self.image_dropdown['values'] = apod_desktop.get_all_apod_titles()

    def get_apod(self):
        date_str = self.date_var.get()
        try:
            apod_date = date.fromisoformat(date_str)
        except ValueError:
            self.show_error("Invalid date format. Use YYYY-MM-DD.")
            return

        first_apod_date = date(1995, 6, 16)
        if apod_date < first_apod_date or apod_date > date.today():
            self.show_error("Date must be between 1995-06-16 and today.")
            return

        apod_desktop.init_apod_cache()
        apod_id = apod_desktop.add_apod_to_cache(apod_date)
        if apod_id != 0:
            apod_info = apod_desktop.get_apod_info(apod_id)
            self.display_image(apod_info['file_path'])
            self.explanation_text.delete('1.0', tk.END)
            self.explanation_text.insert(tk.END, apod_info['explanation'])
            self.load_apod_list()
        else:
            self.show_error("Failed to retrieve APOD.")

    def show_selected_apod(self, event):
        title = self.image_dropdown.get()
        if title:
            conn = apod_desktop.sqlite3.connect(apod_desktop.image_cache_db)
            cursor = conn.cursor()
            cursor.execute("SELECT file_path, explanation FROM apod_images WHERE title = ?", (title,))
            result = cursor.fetchone()
            if result:
                file_path, explanation = result
                self.display_image(file_path)
                self.show_explanation(explanation)
                self.title(title)
            conn.close()

    def show_explanation(self, explanation):
        self.explanation_text.delete('1.0', tk.END)
        self.explanation_text.insert(tk.END, explanation)
        self.explanation_text.grid()

    def display_image(self, image_path):
        image = Image.open(image_path)
        width, height = image.size
        max_height = 300  # Set the desired maximum height
        if height > max_height:
            new_width = int(width * (max_height / height))
            new_height = max_height
            resized_image = image.resize((new_width, new_height), resample=Image.Resampling.LANCZOS)
        else:
            resized_image = image
        photo_image = ImageTk.PhotoImage(resized_image)
        self.image_label.configure(image=photo_image)
        self.image_label.image = photo_image  # Keep a reference to prevent garbage collection

    def set_desktop_background(self):
        title = self.image_dropdown.get()
        if title:
            conn = apod_desktop.sqlite3.connect(apod_desktop.image_cache_db)
            cursor = conn.cursor()
            cursor.execute("SELECT file_path FROM apod_images WHERE title = ?", (title,))
            result = cursor.fetchone()
            if result:
                file_path = result[0]
                image_lib.set_desktop_background_image(file_path)
            conn.close()

    def show_error(self, message):
        error_window = tk.Toplevel(self)
        error_window.title("Error")
        error_label = ttk.Label(error_window, text=message)
        error_label.pack(padx=20, pady=20)
        ok_button = ttk.Button(error_window, text="OK", command=error_window.destroy)
        ok_button.pack(pady=10)


if __name__ == "__main__":
    app = APODViewer()
    app.mainloop()