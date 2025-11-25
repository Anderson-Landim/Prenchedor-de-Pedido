import tkinter as tk
from ctypes import (
    Structure, POINTER, sizeof, c_int, c_uint,
    c_void_p, windll, byref, addressof
)


# --- Estruturas ---
class ACCENT_POLICY(Structure):
    _fields_ = [
        ("AccentState", c_int),
        ("AccentFlags", c_int),
        ("GradientColor", c_int),
        ("AnimationId", c_int)
    ]


class WINCOMPATTRDATA(Structure):
    _fields_ = [
        ("Attribute", c_int),
        ("Data", c_void_p),
        ("SizeOfData", c_uint)
    ]


# --- Blur/Acrylic ---
def apply_blur(hwnd):
    accent = ACCENT_POLICY()
    accent.AccentState = 4  # ACCENT_ENABLE_ACRYLICBLURBEHIND
    accent.GradientColor = 0x99FFFFFF  # Transparência + cor (ARGB)

    accent_data = WINCOMPATTRDATA()
    accent_data.Attribute = 19  # WCA_ACCENT_POLICY
    accent_data.Data = c_void_p(addressof(accent))
    accent_data.SizeOfData = sizeof(accent)

    windll.user32.SetWindowCompositionAttribute(hwnd, byref(accent_data))


# ------------ TKINTER ------------
root = tk.Tk()
root.geometry("600x400")
root.title("Acrylic Blur Topmost Test")

root.update_idletasks()
hwnd = root.winfo_id()

apply_blur(hwnd)

# 🔥 Mantém sempre por cima
root.attributes("-topmost", True)

tk.Label(root, text="Acrylic Blur + Sempre por Cima", font=("Segoe UI", 18)).pack(pady=50)

root.mainloop()
