import os, requests, re, json, xml.etree.ElementTree as ET
from datetime import datetime

REPO_PATH = os.path.abspath(os.path.dirname(__file__))
FILES = {
    "law": os.path.join(REPO_PATH, "ukraine_law_runtime_status.json"),
    "sanctions": os.path.join(REPO_PATH, "sanctions_status.json"),
    "logs": os.path.join(REPO_PATH, "logs"),
}

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID", "YOUR_CHAT_ID")

URLS = {
    "constitution": "https://zakon.rada.gov.ua/laws/show/254к/96-вр",
    "criminal_code": "https://zakon.rada.gov.ua/laws/show/2341-14",
    "civil_code": "https://zakon.rada.gov.ua/laws/show/435-15",
    "nacp_api": "https://public.nazk.gov.ua/public_api",
    "ofsi": "https://www.gov.uk/government/collections/uk-sanctions-on-russia.atom",
    "ofac": "https://ofac.treasury.gov/rss.xml",
}

# ---------------- PARSING UTILITIES ---------------- #

def get_rada_date(html):
    """
    Универсальный парсер даты редакции.
    Работает даже если изменится структура страницы.
    """
    # пример: "Редакція від 18.11.2025"
    m = re.search(r"Редакція від\s*(\d{2}\.\d{2}\.\d{4})", html)
    if m:
        try:
            return datetime.strptime(m.group(1), "%d.%m.%Y").strftime("%Y-%m-%d")
        except:
            pass

    # запасной вариант — если Рада поменяет HTML
    m = re.search(r"(\d{2}\.\d{2}\.\d{4})", html)
    if m:
        try:
            return datetime.strptime(m.group(1), "%d.%m.%Y").strftime("%Y-%m-%d")
        except:
            pass

    return None


def fetch_rada(url):
    try:
        html = requests.get(url, timeout=25).text
        return get_rada_date(html)
    except:
        return None


def check_api(url):
    try:
        return requests.head(url, timeout=15).status_code == 200
    except:
        return False


def fetch_feed_titles(feed_url, is_atom=True):
    try:
        xml_data = requests.get(feed_url, timeout=25).text
        root = ET.fromstring(xml_data)

        if is_atom:
            titles = [el.text for el in root.findall(".//{http://www.w3.org/2005/Atom}title") if el.text]
        else:
            titles = [el.text for el in root.findall(".//title") if el.text]

        return titles[:10]
    except:
        return []


def send_tg(msg):
    if "YOUR_TELEGRAM_BOT_TOKEN" in BOT_TOKEN:
        return

    try:
        api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(api, json={"chat_id": CHAT_ID, "text": msg}, timeout=15)
    except:
        pass


def load_prev(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------- MAIN ---------------- #

def main():
    send_tg("✅ Тестовое уведомление: система мониторинга активна.")

    law_report = {
        "timestamp": datetime.now().isoformat(),
        "constitution_last": fetch_rada(URLS["constitution"]),
        "criminal_code_last": fetch_rada(URLS["criminal_code"]),
        "civil_code_last": fetch_rada(URLS["civil_code"]),
        "nacp_api_ok": check_api(URLS["nacp_api"]),
    }

    sanctions_report = {
        "timestamp": datetime.now().isoformat(),
        "ofsi_titles": fetch_feed_titles(URLS["ofsi"], is_atom=True),
        "ofac_titles": fetch_feed_titles(URLS["ofac"], is_atom=True),
    }

    prev_law = load_prev(FILES["law"])
    prev_sanctions = load_prev(FILES["sanctions"])

    alerts = []

    # УКРАИНСКИЕ ЗАКОНЫ
    if prev_law.get("constitution_last") != law_report["constitution_last"]:
        if law_report["constitution_last"]:
            alerts.append(
                f"⚖️ Конституция Украины — новая редакция ({law_report['constitution_last']}).\n"
                f"🔗 {URLS['constitution']}"
            )

    if prev_law.get("criminal_code_last") != law_report["criminal_code_last"]:
        if law_report["criminal_code_last"]:
            alerts.append(
                f"⚖️ Уголовный кодекс — обновление ({law_report['criminal_code_last']}).\n"
                f"🔗 {URLS['criminal_code']}"
            )

    if prev_law.get("civil_code_last") != law_report["civil_code_last"]:
        if law_report["civil_code_last"]:
            alerts.append(
                f"⚖️ Гражданский кодекс — новая редакция ({law_report['civil_code_last']}).\n"
                f"🔗 {URLS['civil_code']}"
            )

    if not law_report["nacp_api_ok"]:
        alerts.append("❌ API НАЗК недоступен.")

    # САНКЦИИ
    if (
        prev_sanctions.get("ofsi_titles")
        and sanctions_report["ofsi_titles"]
        and sanctions_report["ofsi_titles"][0] != prev_sanctions["ofsi_titles"][0]
    ):
        alerts.append("🇬🇧 OFSI: новое обновление санкций.")

    if (
        prev_sanctions.get("ofac_titles")
        and sanctions_report["ofac_titles"]
        and sanctions_report["ofac_titles"][0] != prev_sanctions["ofac_titles"][0]
    ):
        alerts.append("🇺🇸 OFAC: новые санкции.")

    save(FILES["law"], law_report)
    save(FILES["sanctions"], sanctions_report)

    # отправка уведомлений
    if alerts:
        log_path = os.path.join(
            FILES["logs"], f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        save(
            log_path,
            {
                "timestamp": datetime.now().isoformat(),
                "alerts": alerts,
                "laws": law_report,
                "sanctions": sanctions_report,
            },
        )

        send_tg("📢 Project Thread — обновления:\n\n" + "\n\n".join(alerts))


if __name__ == "__main__":
    main()

