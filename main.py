import os
import time
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.clock import Clock
from kivy.utils import platform
import fitz  # PyMuPDF

class PDFProcessor(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.chooser = FileChooserIconView(filters=["*.pdf"])
        self.add_widget(self.chooser)

        self.output_label = Label(text="Select a PDF to process.")
        self.add_widget(self.output_label)

        process_btn = Button(text="Process PDF")
        process_btn.bind(on_release=self.process_pdf)
        self.add_widget(process_btn)

    def process_pdf(self, instance):
        selected = self.chooser.selection
        if not selected:
            self.output_label.text = "No file selected."
            return

        input_path = selected[0]
        # Determine the output path
        if platform == 'android':
            from android.storage import app_storage_path
            output_dir = app_storage_path()
        else:
            output_dir = os.path.expanduser("~")

        output_filename = os.path.basename(input_path).replace(".pdf", "_processed.pdf")
        output_path = os.path.join(output_dir, output_filename)

        self.output_label.text = "Processing..."

        threading.Thread(target=self.invert_pdf, args=(input_path, output_path)).start()

    def invert_pdf(self, input_pdf, output_pdf):
        start = time.time()
        doc = fitz.open(input_pdf)
        new_doc = fitz.open()

        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=100)
            img = bytearray(pix.samples)

            for j in range(0, len(img), pix.n):
                r, g, b = img[j], img[j + 1], img[j + 2]
                if (r, g, b) == (255, 255, 255):
                    img[j:j + 3] = b'\x00\x00\x00'
                else:
                    img[j:j + 3] = b'\xff\xff\xff'

            new_pix = fitz.Pixmap(fitz.csRGB, pix.width, pix.height, bytes(img))
            page_rect = page.rect
            img_page = new_doc.new_page(width=page_rect.width, height=page_rect.height)
            img_page.insert_image(page_rect, pixmap=new_pix)

            Clock.schedule_once(lambda dt, i=i: self.update_status(i + 1, len(doc)), 0)

        new_doc.save(output_pdf, deflate=True)
        elapsed = time.time() - start
        Clock.schedule_once(lambda dt: self.output_label.setter('text')(self.output_label, f"Done in {elapsed:.2f} seconds\nSaved to {output_pdf}"), 0)

    def update_status(self, current, total):
        self.output_label.text = f"Processed page {current}/{total}"

class PDFApp(App):
    def build(self):
        return PDFProcessor()

if __name__ == "__main__":
    PDFApp().run()
