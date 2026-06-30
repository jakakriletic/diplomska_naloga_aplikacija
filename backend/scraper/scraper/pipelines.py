"""Modul za ČIŠČENJE in osnovno pripravo zajetih podatkov.

Iz surove HTML kode odstrani nepotrebne elemente (navigacija, noga, skripte,
piškotki, prijavni/iskalni obrazci, družbena omrežja ...) in vrne le smiselno
besedilno vsebino, primerno za nadaljnjo obdelavo (chunking + AI).
"""
from itemadapter import ItemAdapter
from bs4 import BeautifulSoup

# Strukturni elementi, ki praviloma ne vsebujejo vsebinskih podatkov
STRIP_TAGS = [
    "style", "script", "noscript", "svg", "iframe",
    "nav", "header", "footer", "aside", "form",
]

# Ključne besede v id/class, ki označujejo nevsebinske gradnike
NOISE_KEYWORDS = [
    "cookie", "cookies", "cookienotice", "cookie-notice", "cookieconsent",
    "cookie-consent", "cookiebanner", "cookie-banner", "cookiebar", "cookie-bar",
    "piškot", "piškotek", "piškotki", "piskot", "piskotek", "piskotki", "gdpr",
    "consent", "copyright", "search", "search-form", "searchbox", "search-box",
    "iskanje", "login", "signin", "sign-in", "register", "registration",
    "prijava", "registracija", "newsletter", "subscribe", "subscription",
    "social", "socials", "social-links", "share", "sharing", "facebook",
    "instagram", "linkedin", "twitter", "youtube", "tiktok", "tracking",
    "analytics", "gtm", "google-analytics", "googletagmanager", "fb-pixel",
    "pixel", "modal", "popup", "pop-up", "overlay", "breadcrumb", "menu",
]


class CleaningPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        html = adapter.get("html")

        if not isinstance(html, str):
            return item

        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(STRIP_TAGS):
            tag.decompose()

        to_delete = []
        for element in soup.find_all(True):
            element_id = element.get("id", "")
            element_class = " ".join(element.get("class", []))
            joined = f"{element_id} {element_class}".lower()
            if any(noise in joined for noise in NOISE_KEYWORDS):
                to_delete.append(element)

        for element in to_delete:
            element.decompose()

        adapter["html"] = " ".join(soup.stripped_strings)
        return item
