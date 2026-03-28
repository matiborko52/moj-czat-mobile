import flet as ft
import requests
import time
import threading

URL_BAZY = "https://mojczat-19ddf-default-rtdb.europe-west1.firebasedatabase.app/"

def main(page: ft.Page):
    page.title = "MojCzat GOD MODE"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 420
    page.window_height = 800
    page.padding = 0
    
    user_data = {"nick": None, "rola": "user", "kolor": "#ffffff", "prefix": "", "kod": None}
    last_data = [None]
    refresh_thread = [None]

    chat_list = ft.ListView(expand=True, spacing=10, auto_scroll=True, padding=15)
    msg_input = ft.TextField(hint_text="Napisz wiadomość...", expand=True, border_radius=20, bgcolor="#2f3640", on_submit=lambda e: send_msg())

    def show_snack(text, color="red"):
        page.snack_bar = ft.SnackBar(ft.Text(text), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def login_process(e):
        kod = login_input.value
        try:
            res = requests.get(f"{URL_BAZY}/konta/{kod}.json").json()
            if res:
                user_data.update(res)
                user_data["kod"] = kod
                build_chat_view()
                page.go("/chat")
                if refresh_thread[0] is None:
                    refresh_thread[0] = threading.Thread(target=refresh_loop, daemon=True)
                    refresh_thread[0].start()
            else: show_snack("Zły kod!")
        except: show_snack("Błąd połączenia!")

    def send_msg():
        if not msg_input.value.strip(): return
        d_name = f"{user_data['prefix']} {user_data['nick']}".strip()
        m = {"autor": d_name, "wiadomosc": msg_input.value, "kolor": user_data['kolor'], "time": time.time()}
        requests.post(f"{URL_BAZY}/chat.json", json=m)
        msg_input.value = ""
        page.update()

    def refresh_loop():
        while True:
            try:
                res = requests.get(f"{URL_BAZY}/chat.json").json()
                if res != last_data[0]:
                    last_data[0] = res
                    chat_list.controls.clear()
                    if res:
                        for k in res:
                            m = res[k]
                            chat_list.controls.append(ft.Column([
                                ft.Text(m.get('autor',''), color=m.get('kolor','#fff'), weight="bold"),
                                ft.Container(content=ft.Text(m.get('wiadomosc',''), color="white"), bgcolor="#2f3640", padding=10, border_radius=10)
                            ]))
                    page.update()
            except: pass
            time.sleep(2)

    login_input = ft.TextField(label="Kod dostępu", password=True, on_submit=login_process)
    
    def build_chat_view():
        page.views.append(ft.View("/chat", [
            ft.AppBar(title=ft.Text("MojCzat", color="#00d8d6"), bgcolor="#2f3640"),
            chat_list,
            ft.Container(content=ft.Row([msg_input, ft.IconButton(ft.icons.SEND, on_click=lambda e: send_msg())]), padding=10)
        ]))

    page.on_route_change = lambda r: page.update()
    page.views.append(ft.View("/", [ft.Column([ft.Text("M O J C Z A T", size=30), login_input, ft.ElevatedButton("WEJDŹ", on_click=login_process)], alignment="center")], vertical_alignment="center"))
    page.go("/")

ft.app(target=main)
