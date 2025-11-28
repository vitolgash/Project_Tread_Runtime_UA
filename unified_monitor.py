import os, requests, re, json, xml.etree.ElementTree as ET
from datetime import datetime

REPO_PATH = os.path.abspath(os.path.dirname(__file__))
FILES = {
    "law": os.path.join(REPO_PATH, "ukraine_law_runtime_status.json"),
    "sanctions": os.path.join(REPO_PATH, "sanctions_status.json"),
    "logs": os.path.join(REPO_PATH, "logs")
}

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID", "YOUR_CHAT_ID")

URLS = {
    "constitution": "https://zakon.rada.gov.ua/laws/show/254%D0%BA/96-%D0%B2%D1%80",
    "criminal_code": "https://zakon.rada.gov.ua/laws/show/2341-14",
    "civil_code": "https://zakon.rada.gov.ua/laws/show/435-15",
    "nacp_api": "https://public.nazk.gov.ua/public_api",
    "ofsi": "https://www.gov.uk/government/collections/uk-sanctions-on-russia.atom",
    "ofac": "https://ofac.treasury.gov/rss.xml"
}


def fetch_last_edit(url, pattern=r"редакція від\s(\d{2}\.\d{2}\.\d{4})"):
    try:
        html = requests.get(url, timeout=25).text
        m = re.search(pattern, html)
        if m:
            return datetime.strptime(m.group(1), "%d.%m.%Y").strftime("%Y-%m-%d")
    except Exception:
        return None


def check_api(url):
    try:
        return requests.head(url, timeout=15).status_code == 200
    except Exception:
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
    except Exception:
        return []


def send_tg(msg: str):
    if "YOUR_TELEGRAM_BOT_TOKEN" in BOT_TOKEN or "YOUR_CHAT_ID" in CHAT_ID:
        return
    try:
        api = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(api, json={"chat_id": CHAT_ID, "text": msg}, timeout=15)
    except Exception:
        pass


def load_prev(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    send_tg("✅ Тестовое уведомление: система мониторинга активна.")

    law_report = {
        "timestamp": datetime.now().isoformat(),
        "constitution_last": fetch_last_edit(URLS["constitution"]),
        "criminal_code_last": fetch_last_edit(URLS["criminal_code"]),
        "civil_code_last": fetch_last_edit(URLS["civil_code"]),
        "nacp_api_ok": check_api(URLS["nacp_api"])
    }

    sanctions_report = {
        "timestamp": datetime.now().isoformat(),
        "ofsi_titles": fetch_feed_titles(URLS["ofsi"], is_atom=True),
        "ofac_titles": fetch_feed_titles(URLS["ofac"], is_atom=True)
    }

    prev_law = load_prev(FILES["law"])
    prev_sanctions = load_prev(FILES["sanctions"])

    alerts = []

    if prev_law.get("constitution_last") != law_report["constitution_last"] and law_report["constitution_last"]:
        alerts.append("⚖️ Конституция Украины обновлена.")

    if prev_law.get("criminal_code_last") != law_report["criminal_code_last"] and law_report["criminal_code_last"]:
        alerts.append("⚖️ Изменён Уголовный кодекс Украины.")

    if prev_law.get("civil_code_last") != law_report["civil_code_last"] and law_report["civil_code_last"]:
        alerts.append("⚖️ Обновлён Гражданский кодекс Украины.")

    if not law_report["nacp_api_ok"]:
        alerts.append("❌ API НАЗК недоступен.")

    if prev_sanctions.get("ofsi_titles") and sanctions_report["ofsi_titles"] and sanctions_report["ofsi_titles"][0] != prev_sanctions["ofsi_titles"][0]:
        alerts.append("🇬🇧 OFSI: новое обновление санкций.")

    if prev_sanctions.get("ofac_titles") and sanctions_report["ofac_titles"] and sanctions_report["ofac_titles"][0] != prev_sanctions["ofac_titles"][0]:
        alerts.append("🇺🇸 OFAC: новые санкции.")

    save(FILES["law"], law_report)
    save(FILES["sanctions"], sanctions_report)

    if alerts:
        log_path = os.path.join(FILES["logs"], f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        save(log_path, {
            "timestamp": datetime.now().isoformat(),
            "alerts": alerts,
            "law": law_report,
            "sanctions": sanctions_report
        })

        send_tg("Project Tread — обновления:\n" + "\n".join(alerts))

    print(json.dumps({
        "laws": law_report,
        "sanctions": sanctions_report
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
