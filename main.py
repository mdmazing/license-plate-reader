import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import pytesseract
import cv2
import os
import numpy as np

# SET TESSERACT PATH
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

plate_preview = None  # Global for updating preview

# OCR function
def process_image(image_path):
    global plate_preview

    try:
        # Load image
        img_color = cv2.imread(image_path)
        img_color = cv2.resize(img_color, (600, int(img_color.shape[0] * (600 / img_color.shape[1]))))

        img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
        edged = cv2.Canny(img_gray, 170, 200)

        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]

        plate_color = None
        plate_gray = None

        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                if 2 < aspect_ratio < 6:
                    plate_color = img_color[y:y+h, x:x+w]
                    plate_gray = img_gray[y:y+h, x:x+w]
                    break

        if plate_color is None or plate_gray is None:
            raise Exception("License plate not found")

        # Show cropped COLOR plate preview
        pil_image = Image.fromarray(cv2.cvtColor(plate_color, cv2.COLOR_BGR2RGB))
        pil_image = pil_image.resize((250, 80), Image.LANCZOS)
        plate_preview = ImageTk.PhotoImage(pil_image)
        plate_label.config(image=plate_preview)

        # Threshold GRAYSCALE plate for OCR
        _, plate_thresh = cv2.threshold(plate_gray, 127, 255, cv2.THRESH_BINARY)

        # Save temp plate for OCR
        temp_plate_path = "temp_plate.png"
        cv2.imwrite(temp_plate_path, plate_thresh)

        # OCR the temp_plate.png
        image = Image.open(temp_plate_path)
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        text = pytesseract.image_to_string(image, config=custom_config).strip()

        if not text:
            raise Exception("No text found on the plate")

        # Show extracted text
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, text)

        # Save extracted text to file
        output_path = os.path.splitext(image_path)[0] + "_output.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

        messagebox.showinfo("Success", f"Plate text saved to:\n{output_path}")

    except Exception as e:
        messagebox.showerror("Error", str(e))

# Upload image
def upload_image():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
    if file_path:
        process_image(file_path)

# Copy text to clipboard
def copy_text():
    text = text_area.get("1.0", tk.END).strip()
    if text:
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        messagebox.showinfo("Copied", "Text copied to clipboard!")

# GUI setup
root = tk.Tk()
root.title("License Plate Reader")
root.geometry("600x600")
root.configure(bg="#f0f0f0")
root.resizable(False, False)

# Title label
title_label = tk.Label(root, text="License Plate Reader", font=("Arial", 24, "bold"), bg="#f0f0f0")
title_label.pack(pady=10)

# Upload button
upload_btn = tk.Button(root, text="Upload Image", command=upload_image, font=("Arial", 16), width=20, bg="#4CAF50", fg="white")
upload_btn.pack(pady=10)

# Plate preview label
plate_label = tk.Label(root, bg="#f0f0f0")
plate_label.pack(pady=10)

# Frame for text area
frame = tk.Frame(root, bg="#ffffff", bd=2, relief=tk.GROOVE)
frame.pack(padx=20, pady=10, fill="both", expand=True)

# Text area inside frame
text_area = tk.Text(frame, height=8, font=("Courier", 16), wrap="word", bg="#ffffff", relief=tk.FLAT)
text_area.pack(padx=10, pady=10, fill="both", expand=True)

# Copy button
copy_btn = tk.Button(root, text="Copy to Clipboard", command=copy_text, font=("Arial", 14), width=20, bg="#2196F3", fg="white")
copy_btn.pack(pady=10)

root.mainloop()
