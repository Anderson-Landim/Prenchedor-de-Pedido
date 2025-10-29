"""
App Tkinter + Ttkbootstrap com lista fixa persistida em JSON.
- Itens concluídos ficam verdes e o scroll avança automaticamente
- Salva alterações (adicionar/editar/excluir) em 'dados.json'
"""

import threading
import time
import json
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *

try:
    import pyautogui
except Exception:
    pyautogui = None


JSON_PATH = Path("dados.json")

LISTA_PADRAO = [
    ("111088", "RESIDUO FONDUE DE QUEIJO"),
    ("111089", "RESIDUO FONDUE DE QUEIJO AZUL DE MINAS"),
    ("111127", "RESIDUOS QUEIJO SANTO CASAMENTEIRO"),
    ("111128", "RESIDUOS QUEIJO MATURADO COM MOFO AZUL"),
    ("111129", "RESIDUOS QUEIJO AZUL DE MINAS"),
    ("111130", "RESIDUOS QUEIJO VERSOS DE MINAS"),
    ("111131", "RESIDUOS MASSA DE RICOTA"),
    ("111132", "RESIDUOS QUEIJO BRIE FORMA"),
    ("111135", "RESIDUOS QUEIJO CAMEMBERT"),
    ("111139", "RESIDUOS QUEIJO COALHO PECA"),
    ("111141", "RESIDUOS QJ PREPARADO FONDUE"),
    ("111145", "RESIDUOS QUEIJO MUSSARELA OREGANO PARA FRACIONAR"),
    ("111146", "RESIDUOS QUEIJO MUSSARELA PIMENTA PARA FRACIONAR"),
    ("111148", "RESIDUOS QUEIJO PROVOLONE PALITO ST"),
    ("111153", "RESIDUOS QUEIJO DANBO A LENDA"),
    ("111154", "RESIDUOS QUEIJO DAMBO A LENDA PARA FRACIONAR"),
    ("111156", "RESIDUOS QUEIJO MINAS PADRAO"),
    ("111159", "RESIDUOS QUEIJO SERRA DA MANTIQUEIRA"),
    ("111162", "RESIDUOS QUEIJO GOUDA"),
    ("111163", "RESIDUOS QUEIJO GOUDA PARA FATIAR"),
    ("111166", "RESIDUOS QUEIJO ESTEPE PARA FRACIONAR"),
    ("111167", "RESIDUOS QUEIJO PRATO ESFERICO PARA FRACIONAR"),
    ("111168", "RESIDUOS QUEIJO EMMENTAL"),
    ("111169", "RESIDUOS QUEIJO EMMENTAL 6 KG"),
    ("111171", "RESIDUOS QUEIJO GRUYERE"),
    ("111172", "RESIDUOS QUEIJO GRUYERE 6 KG"),
    ("111174", "RESIDUOS QUEIJO GRUYERE PARA PROCESSAR"),
    ("111175", "RESIDUOS QUEIJO MUSSARELA"),
    ("111187", "RESIDUO DE SORO DE LEITE"),
    ("111211", "RESIDUOS MOZZARELLA DE BÚFALA"),
]


class CodeStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = []
        self.load()

    def load(self):
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as f:
                    raw = json.load(f)
                cleaned = []
                for item in raw:
                    if isinstance(item, dict):
                        cod = str(item.get("codigo", "")).strip()
                        nome = str(item.get("nome", "")).strip()
                    elif isinstance(item, (list, tuple)) and len(item) >= 1:
                        cod = str(item[0]).strip()
                        nome = str(item[1]).strip() if len(item) > 1 else ""
                    else:
                        continue
                    if cod:
                        cleaned.append((cod, nome))
                self.data = cleaned if cleaned else LISTA_PADRAO.copy()
            except Exception as e:
                print(f"[CodeStore] Erro lendo JSON: {e}")
                self.data = LISTA_PADRAO.copy()
        else:
            self.data = LISTA_PADRAO.copy()
            self.save()

    def save(self):
        try:
            out = [{"codigo": c, "nome": n} for c, n in self.data]
            with self.path.open("w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CodeStore] Erro salvando JSON: {e}")

    def get_all(self):
        return self.data

    def add(self, codigo, nome):
        self.data.append((codigo, nome))
        self.save()

    def edit(self, idx, codigo, nome):
        if 0 <= idx < len(self.data):
            self.data[idx] = (codigo, nome)
            self.save()

    def delete(self, idx):
        if 0 <= idx < len(self.data):
            del self.data[idx]
            self.save()


class AutoTyperApp(tb.Window):
    def __init__(self):
        super().__init__(themename="superhero")
        self.title("Automação de pedido de Residuo")
        self.geometry("550x900")

        self.store = CodeStore(JSON_PATH)
        self.stop_event = threading.Event()
        self.worker = None
        self.cards = []  # referência dos cards (para mudar cor)

        self._build_ui()

    def _build_ui(self):
        title = tb.Label(self, text="📋 Lista de Códigos", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(15, 10))

        container = tb.Frame(self)
        container.pack(fill=BOTH, expand=True, padx=20)

        self.canvas = tk.Canvas(container, highlightthickness=0)
        self.scroll_frame = tb.Frame(self.canvas)
        vsb = tb.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        bar = tb.Frame(self)
        bar.pack(fill=X, pady=10)

        tb.Button(bar, text="➕ Adicionar", bootstyle="success", command=self._add_item, width=15).pack(side="left", padx=10)
        tb.Button(bar, text="▶️ Iniciar", bootstyle="primary", command=self._start, width=15).pack(side="left", padx=10)
        tb.Button(bar, text="⏹ Parar", bootstyle="danger", command=self._stop, width=15).pack(side="left", padx=10)

        self.status = tk.StringVar(value="Pronto")
        tb.Label(self, textvariable=self.status, anchor="w", bootstyle="secondary").pack(fill="x", padx=20, pady=(6, 8))

        self._update_cards()

    def _update_cards(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        self.cards.clear()

        for idx, (codigo, nome) in enumerate(self.store.get_all()):
            card = tk.Frame(self.scroll_frame, bg="white", padx=10, pady=10)
            card.pack(fill=X, pady=4, padx=5)
            self.cards.append(card)

            left = tb.Frame(card)
            left.pack(side="left", fill="both", expand=True)
            tb.Label(left, text=f"{codigo}", font=("Consolas", 11, "bold")).pack(anchor="w")
            tb.Label(left, text=f"{nome}", font=("Segoe UI", 10), foreground="#FFFFFF").pack(anchor="w")


            right = tb.Frame(card)
            right.pack(side="right")

            tb.Button(right, text="Editar", bootstyle="info-outline", width=9,
                      command=lambda i=idx: self._edit_item(i)).pack(side="top", pady=2)
            tb.Button(right, text="Excluir", bootstyle="danger-outline", width=9,
                      command=lambda i=idx: self._delete_item(i)).pack(side="top", pady=2)

    def _add_item(self):
        codigo = tb.dialogs.Querybox.get_string("Digite o código:", "Adicionar novo código")
        if not codigo:
            return
        nome = tb.dialogs.Querybox.get_string("Digite o nome/descritivo:", "Adicionar novo código") or ""
        self.store.add(codigo.strip(), nome.strip())
        self._update_cards()

    def _edit_item(self, idx):
        codigo, nome = self.store.get_all()[idx]
        novo_codigo = tb.dialogs.Querybox.get_string("Editar código:", initialvalue=codigo)
        if not novo_codigo:
            return
        novo_nome = tb.dialogs.Querybox.get_string("Editar descrição:", initialvalue=nome) or ""
        self.store.edit(idx, novo_codigo.strip(), novo_nome.strip())
        self._update_cards()

    def _delete_item(self, idx):
        codigo, nome = self.store.get_all()[idx]
        if messagebox.askyesno("Confirmar exclusão", f"Deseja remover {codigo} - {nome}?"):
            self.store.delete(idx)
            self._update_cards()

    def _start(self):
        if pyautogui is None:
            messagebox.showerror("Erro", "pyautogui não está instalado. pip install pyautogui")
            return
        if not self.store.get_all():
            messagebox.showwarning("Aviso", "Nenhum item na lista.")
            return

        self.stop_event.clear()
        self.status.set("Iniciando em 3 segundos...")
        threading.Thread(target=self._worker, daemon=True).start()

    def _stop(self):
        self.stop_event.set()
        self.status.set("Parando...")

    def _worker(self):
        time.sleep(3)
        pyautogui.FAILSAFE = True
        try:
            for idx, (codigo, _) in enumerate(self.store.get_all()):
                if self.stop_event.is_set():
                    break
                self.status.set(f"[{idx+1}/{len(self.store.get_all())}] Digitando: {codigo}")

                # destaca card ativo
                self.after(0, lambda i=idx: self._highlight_card(i, "#1e88e5"))  # azul ativo
                self.after(100, lambda i=idx: self._scroll_to_card(i))

                # automação
                pyautogui.typewrite(codigo)
                for _ in range(5):
                    pyautogui.press("enter")
                pyautogui.typewrite("100")
                pyautogui.press("down")
                for _ in range(8):
                    pyautogui.press("left")
                pyautogui.press("enter")

                # marca como concluído
                self.after(0, lambda i=idx: self._highlight_card(i, "#2e7d32"))  # verde
                time.sleep(0.6)

            self.status.set("✅ Concluído com sucesso.")
        except pyautogui.FailSafeException:
            self.status.set("Abortado: Fail-safe acionado (mova o cursor ao canto superior esquerdo).")
        except Exception as e:
            self.status.set(f"Erro durante execução: {e}")
        finally:
            self.stop_event.clear()

    def _highlight_card(self, idx, color):
        try:
            if 0 <= idx < len(self.cards):
                self.cards[idx].configure(bootstyle=None)
                self.cards[idx].configure(background=color)
                for child in self.cards[idx].winfo_children():
                    child.configure(background=color)
        except Exception as e:
            print(f"Erro ao destacar card: {e}")

    def _scroll_to_card(self, idx):
        if 0 <= idx < len(self.cards):
            self.canvas.yview_moveto(idx / max(1, len(self.cards)))

if __name__ == "__main__":
    app = AutoTyperApp()
    app.mainloop()
