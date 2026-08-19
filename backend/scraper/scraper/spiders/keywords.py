"""Ključne besede za prepoznavanje vsebinsko relevantnih (pod)strani.

Uporabljajo se za PRIORITIZACIJO obiska povezav (ne za strogo filtriranje),
da v okviru omejitve števila strani najprej zajamemo najbolj relevantne vsebine
(o podjetju, kontakt, dejavnost, storitve ...). Večjezično.
"""

KEYWORDS = [
    # Splošno / EN
    "about", "about-us", "company", "company-profile", "who-we-are", "profile",
    "history", "mission", "vision", "team", "management", "leadership",
    "contact", "contact-us", "location", "headquarters", "services", "solutions",
    "products", "industries", "clients", "partners", "references", "certificates",
    "quality",
    # SLO
    "o-nas", "o-podjetju", "podjetje", "druzba", "družba", "kdo-smo",
    "predstavitev", "zgodovina", "poslanstvo", "vizija", "vrednote", "ekipa",
    "vodstvo", "uprava", "poslovodstvo", "organiziranost", "organi", "kontakt",
    "lokacija", "naslov", "sedez", "sedež",
    "storitve", "resitve", "rešitve", "izdelki", "dejavnost", "dejavnosti",
    "partnerji", "reference", "certifikati", "kakovost", "predstavitev-podjetja",
    "o-fakulteti", "o_fakulteti", "o-soli", "o-šoli", "studij", "študij", "programi",
    "zaposleni", "raziskave",
    # HR/SR
    "o-nama", "kompanija", "tvrtka", "preduzece", "preduzeće", "tko-smo",
    "ko-smo", "misija", "povijest", "istorija", "rukovodstvo", "adresa",
    "usluge", "proizvodi", "delatnost", "djelatnost",
    # DE
    "uber-uns", "ueber-uns", "unternehmen", "firma", "firmenprofil",
    "geschichte", "mitarbeiter", "standort", "adresse", "dienstleistungen",
    "produkte", "kunden", "referenzen",
    # IT / FR / ES
    "chi-siamo", "azienda", "contatti", "servizi", "prodotti",
    "qui-sommes-nous", "entreprise", "contact", "services", "produits",
    "sobre-nosotros", "empresa", "contacto", "servicios", "productos",
]


# Te povezave naj pajek obišče pred splošnimi vsebinami, saj praviloma vsebujejo
# podatke, ki jih strukturirana ekstrakcija potrebuje za polje »vodstvo«.
HIGH_PRIORITY_KEYWORDS = [
    "vodstvo", "uprava", "poslovodstvo", "management", "leadership", "team",
    "organiziranost", "organi", "o-fakulteti", "o_fakulteti", "about-us",
    "company-profile",
]
