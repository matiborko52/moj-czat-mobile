import flet as ft
import requests
import time
import threading

# --- KONFIGURACJA ---
URL_BAZY = "https://mojczat-19ddf-default-rtdb.europe-west1.firebasedatabase.app/"

def main(page: ft.Page):
    page.title = "MojCzat GOD MODE"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 420
    page.window_height = 800
    page.padding = 0
    
    # Stan aplikacji
    user_data = {"nick": None, "rola": "user", "kolor": "#ffffff", "prefix": "", "kod": None}
    last_data = [None]
    refresh_thread = [None] # Referencja do wątku

    # --- ELEMENTY GŁÓWNE ---
    chat_list = ft.ListView(expand=True, spacing=10, auto_scroll=True, padding=15)
    
    msg_input = ft.TextField(
        hint_text="Napisz wiadomość...", 
        expand=True, 
        border_radius=20,
        filled=True,
        bgcolor="#2f3640",
        border_color="#00d8d6",
        on_submit=lambda e: send_msg()
    )

    # --- FUNKCJE POMOCNICZE (MARKDOWN I KOLORY) ---
    def parse_message_to_spans(text):
        spans = []
        words = text.split(" ")
        for w in words:
            if w.startswith("*") and w.endswith("*"):
                spans.append(ft.TextSpan(w[1:-1] + " ", ft.TextStyle(weight=ft.FontWeight.BOLD)))
            elif w.startswith("_") and w.endswith("_"):
                spans.append(ft.TextSpan(w[1:-1] + " ", ft.TextStyle(italic=True)))
            else:
                spans.append(ft.TextSpan(w + " "))
        return spans

    def show_snack(text, color="red"):
        page.snack_bar = ft.SnackBar(ft.Text(text, color="white"), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    # --- LOGIKA ---
    def login_process(e):
        kod = login_input.value
        try:
            res = requests.get(f"{URL_BAZY}/konta/{kod}.json", timeout=5).json()
            if res:
                user_data.update(res)
                user_data["kod"] = kod
                build_chat_view()
                page.go("/chat")
                # Odpalamy odświeżanie, jeśli jeszcze nie działa
                if refresh_thread[0] is None or not refresh_thread[0].is_alive():
                    refresh_thread[0] = threading.Thread(target=refresh_loop, daemon=True)
                    refresh_thread[0].start()
            else:
                show_snack("Zły kod dostępu!")
        except:
            show_snack("Brak połączenia z chmurą!")

    def send_msg():
        t = msg_input.value
        if not t.strip(): return
        
        # Sprawdzanie MUTE
        try:
            u = requests.get(f"{URL_BAZY}/konta/{user_data['kod']}.json").json()
            poz = int(u.get("mute_until", 0) - time.time())
            if poz > 0:
                show_snack(f"Jesteś wyciszony! Zostało: {poz}s")
                return
        except: pass

        display_name = f"{user_data['prefix']} {user_data['nick']}".strip()
        m = {"autor": display_name, "wiadomosc": t, "kolor": user_data['kolor'], "time": time.time()}
        
        requests.post(f"{URL_BAZY}/chat.json", json=m)
        msg_input.value = ""
        page.update()

    def refresh_loop():
        while True:
            try:
                if page.route != "/chat":
                    time.sleep(1)
                    continue
                    
                res = requests.get(f"{URL_BAZY}/chat.json", timeout=2).json()
                if res != last_data[0]:
                    last_data[0] = res
                    chat_list.controls.clear()
                    if res:
                        for k in res:
                            m = res[k]
                            autor = m.get('autor', 'Anonim')
                            msg = m.get('wiadomosc', '')
                            kolor = m.get('kolor', '#ffffff')
                            
                            chat_list.controls.append(
                                ft.Column([
                                    ft.Text(autor, color=kolor, weight="bold", size=13),
                                    ft.Container(
                                        content=ft.Text(spans=parse_message_to_spans(msg), color="white", size=15),
                                        bgcolor="#2f3640",
                                        padding=10,
                                        border_radius=ft.border_radius.only(top_left=10, top_right=10, bottom_right=10)
                                    )
                                ], spacing=2)
                            )
                    page.update()
            except: pass
            time.sleep(2)

    # --- OKIENKA POP-UP (DIALOGI) ---
    
    # 1. Dialog Zmiany Hasła (User)
    new_key_input = ft.TextField(label="Nowy tajny kod")
    
    def change_user_key(e):
        n = new_key_input.value
        if n:
            d = requests.get(f"{URL_BAZY}/konta/{user_data['kod']}.json").json()
            requests.put(f"{URL_BAZY}/konta/{n}.json", json=d)
            requests.delete(f"{URL_BAZY}/konta/{user_data['kod']}.json")
            user_data['kod'] = n
            show_snack("Twój kod został zmieniony!", "green")
            user_key_dialog.open = False
            page.update()

    user_key_dialog = ft.AlertDialog(
        title=ft.Text("Zmień Klucz"),
        content=new_key_input,
        actions=[ft.TextButton("Zapisz", on_click=change_user_key), ft.TextButton("Anuluj", on_click=lambda e: close_dlg(user_key_dialog))],
    )

    # 2. Dialog Admina
    ad_nick = ft.TextField(label="Nick", height=50)
    ad_kod = ft.TextField(label="Klucz (Hasło)", height=50)
    ad_prefix = ft.TextField(label="Prefix (np. [VIP])", height=50)
    ad_kolor = ft.TextField(label="Kolor (HEX, np. #ff0000)", value="#00d8d6", height=50)
    ad_rola = ft.Dropdown(label="Rola", options=[ft.dropdown.Option("user"), ft.dropdown.Option("admin")], value="user", height=60)
    
    ad_target_kod = ft.TextField(label="Klucz gracza (do MUTE/USUWANIA)", border_color="red")
    ad_mute_sec = ft.TextField(label="Sekundy Mute", input_filter=ft.NumbersOnlyInputFilter())
    ad_new_pass = ft.TextField(label="Zmień mu kod na:")

    def admin_save_user(e):
        d = {"nick": ad_nick.value, "rola": ad_rola.value, "prefix": ad_prefix.value, "kolor": ad_kolor.value}
        requests.put(f"{URL_BAZY}/konta/{ad_kod.value}.json", json=d)
        show_snack("Zapisano profil!", "green")

    def admin_mute_user(e):
        if ad_mute_sec.value and ad_target_kod.value:
            requests.patch(f"{URL_BAZY}/konta/{ad_target_kod.value}.json", json={"mute_until": time.time()+int(ad_mute_sec.value)})
            show_snack(f"Wyciszono na {ad_mute_sec.value}s!", "orange")

    def admin_delete_user(e):
        if ad_target_kod.value:
            requests.delete(f"{URL_BAZY}/konta/{ad_target_kod.value}.json")
            show_snack("Usunięto konto!", "red")

    def admin_force_pass(e):
        if ad_target_kod.value and ad_new_pass.value:
            old = ad_target_kod.value
            n = ad_new_pass.value
            d = requests.get(f"{URL_BAZY}/konta/{old}.json").json()
            if d:
                requests.put(f"{URL_BAZY}/konta/{n}.json", json=d)
                requests.delete(f"{URL_BAZY}/konta/{old}.json")
                show_snack("Zmieniono hasło gracza!", "green")

    admin_dialog = ft.AlertDialog(
        title=ft.Text("Panel Moderacji", color="#ffd32a"),
        content=ft.Column([
            ft.Text("Edycja / Tworzenie", weight="bold"),
            ad_nick, ad_kod, ad_prefix, ad_kolor, ad_rola,
            ft.ElevatedButton("ZAPISZ PROFIL", on_click=admin_save_user, bgcolor="#00d8d6", color="black"),
            ft.Divider(),
            ft.Text("Kary i Zarządzanie", weight="bold", color="red"),
            ad_target_kod, ad_mute_sec,
            ft.ElevatedButton("DAJ MUTE", on_click=admin_mute_user, bgcolor="orange", color="white"),
            ad_new_pass,
            ft.ElevatedButton("ZMIEŃ MU KOD", on_click=admin_force_pass, bgcolor="#4b7cf3", color="white"),
            ft.ElevatedButton("USUŃ KONTO", on_click=admin_delete_user, bgcolor="red", color="white"),
        ], scroll=ft.ScrollMode.AUTO, tight=True),
        actions=[ft.TextButton("Zamknij", on_click=lambda e: close_dlg(admin_dialog))]
    )

    def open_dlg(dlg):
        page.dialog = dlg
        dlg.open = True
        page.update()

    def close_dlg(dlg):
        dlg.open = False
        page.update()

    # --- WIDOKI (EKRANY) ---
    login_input = ft.TextField(label="Twój tajny kod", password=True, text_align="center", border_color="#00d8d6", on_submit=login_process)
    
    login_view = ft.View(
        "/",
        [
            ft.Container(
                content=ft.Column([
                    ft.Text("M O J C Z A T", size=32, weight="bold", color="#00d8d6"),
                    ft.Text("Mobile v7.1 (1:1 PC)", size=14, color="grey"),
                    ft.Divider(height=40, color="transparent"),
                    login_input,
                    ft.ElevatedButton("ZALOGUJ SIĘ", on_click=login_process, bgcolor="#00d8d6", color="#1e272e", width=200, height=50)
                ], alignment="center", horizontal_alignment="center"),
                alignment=ft.alignment.center,
                expand=True
            )
        ],
        bgcolor="#1e272e"
    )

    def build_chat_view():
        appbar_actions = []
        if user_data["rola"] == "admin":
            appbar_actions.append(ft.IconButton(icon=ft.icons.SHIELD, icon_color="#ffd32a", on_click=lambda e: open_dlg(admin_dialog)))
        
        appbar_actions.append(ft.IconButton(icon=ft.icons.KEY, icon_color="#4b7cf3", on_click=lambda e: open_dlg(user_key_dialog)))
        appbar_actions.append(ft.IconButton(icon=ft.icons.LOGOUT, icon_color="red", on_click=lambda e: page.go("/")))

        chat_view = ft.View(
            "/chat",
            [
                ft.AppBar(
                    title=ft.Text(f"{user_data['prefix']} {user_data['nick']}".strip(), size=16, color=user_data['kolor']),
                    bgcolor="#2f3640",
                    actions=appbar_actions
                ),
                chat_list,
                ft.Container(
                    content=ft.Row([
                        msg_input,
                        ft.IconButton(icon=ft.icons.SEND_ROUNDED, icon_color="#00d8d6", icon_size=35, on_click=lambda e: send_msg())
                    ]),
                    padding=10,
                    bgcolor="#1e272e"
                )
            ],
            bgcolor="#1e272e"
        )
        page.views.append(chat_view)

    def route_change(route):
        page.views.clear()
        page.views.append(login_view)
        if page.route == "/chat":
            build_chat_view()
        page.update()

    page.on_route_change = route_change
    page.go("/")

# Uruchomienie
ft.app(target=main)