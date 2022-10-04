roles = ["Informatik", "Audiokommunikation & Technologie", "Technische Informatik", "Wirtschaftsinformatik",
         "Wirtschaftsingenieurwesen", "Physikalische Ingenieurwissenschaften", "Maschinenbau", "Chemieingenieurwesen",
         "Lebensmitteltechnologie", "Biotechnologie", "Audiokommunikation & Technologie",
         "Medientechnik", "Verkehrswesen", "Energie- und Prozesstechnik", "MINTgrün", "Bauingenieurwesen", "Medieninformatik", "Elektrotechnik", "Gast", "EarlyBird"]
metafrage = "Fragen können viel direkter und zielführender beantwortet werden, wenn Du sie klarer und präziser formulierst. z.B: *'Ich verstehe noch nicht ganz, wie ich ein Element im Stack pop-en soll'* statt *'Kann mir jemand mit Stacks helfen?'*\nIm Allgemeinen: **Je präziser die Frage, desto leichter lässt sich eine gute Antwort geben.**\nGenauere Erläuterungen dazu gibt es auf https://metaquestion.net/"

fristen = "https://www.tu.berlin/studierendensekretariat/fristen-termine"

flugvogel = {
    "!vote {message}" : "Fügt thumbsup/down als reaction hinzu",
    "!metafrage" : "Belehrung zu Metafragen",
    "!altklausuren" : "Schickt in einem Modulchannel den passenden Link zur Klausursammlung der Freitagsrunde"
}

channel_ids = {
    "roles" : 1026808696556236853,
    "welcome" : 1026808697000841223,
    "log" : 1026808696556236852,
    "statistiken" : 1026808696556236857
}

role_ids = {
    "admin" : 1026808694870122578,
    "mod" : 1026808694870122577,
    "ban" : 1026808694773649454
}

modul_channel_data ={
    "analina" : {"id" : 963434855356567552, "link" : "https://docs.freitagsrunde.org/Klausuren/Analysis_1_Lineare_Algebra_fuer_Ingenieure_Kombimodul/" },
    "infoprop" : {"id" : 1020283485639938168, "link" : "https://docs.freitagsrunde.org/Klausuren/Informatik-Propädeutikum/"},
    "introprog" : {"id" : 1020283021536010262, "link" : "https://docs.freitagsrunde.org/Klausuren/Einfuehrung_in_die_Programmierung/"},
    "rorg" : {"id" : 1020283202675408986, "link" : "https://docs.freitagsrunde.org/Klausuren/Rechnerorganisation/"},
    "wire" : {"id" : 1020283568305479721, "link" : "https://docs.freitagsrunde.org/Klausuren/Wissenschaftliches_Rechnen/"},
    "logik" : {"id" : 1020283842201931876, "link" : "https://docs.freitagsrunde.org/Klausuren/Logik/"},
    "glet" : {"id" : 900073738341597225, "link" : "not supported"},
    "ana2" : {"id" : 900073755232043098, "link" : "https://docs.freitagsrunde.org/Klausuren/Analysis_2_fuer_Ingenieure/"},
    "swtpp" : {"id" : 1020283745783263353, "link" : "https://docs.freitagsrunde.org/Klausuren/Softwaretechnik_und_Programmierparadigmen/"},
    "diskrete strukturen" : {"id" : 959038568393752616, "link" : "https://docs.freitagsrunde.org/Klausuren/Diskrete_Strukturen/"},
    "algodat" : {"id" : 959038812707766292, "link" : "https://docs.freitagsrunde.org/Klausuren/Algorithmen_und_Datenstrukturen/"},
    "forsa" : {"id" : 959038899567624222, "link" : "https://docs.freitagsrunde.org/Klausuren/Formale_Sprachen_und_Automaten/"},
    "sysprog" : {"id" : 959039171593383966, "link" : "https://docs.freitagsrunde.org/Klausuren/Systemprogrammierung/"},
    "isda" : {"id" : 959039440532144158, "link" : "https://docs.freitagsrunde.org/Klausuren/Informationssysteme%20und%20Datenanalyse/"},
    "elektrische netzwerke" : {"id" : 959039871178145803, "link" : "https://docs.freitagsrunde.org/Klausuren/Elektrische_Netzwerke/"},
    "digitale systeme" : {"id" : 959142783506079794, "link" : "https://docs.freitagsrunde.org/Klausuren/Digitale_Systeme/"},
    "stochastik" : {"id" : 959448765335486565, "link" : "https://docs.freitagsrunde.org/Klausuren/Stochastik_fuer_Informatik/"},
    "itpdg" : {"id" : 1025365508276637726, "link" : "https://docs.freitagsrunde.org/Klausuren/ITPDG_fuer_Ingenieure/"},
    "earlybird" : {"id" : 1002248265217081425, "link" : "https://docs.freitagsrunde.org/Klausuren/Analysis_1_Lineare_Algebra_fuer_Ingenieure_Kombimodul/"},
    "Rechnernetze" : {"id" : 1020284122138157056, "link" : "https://docs.freitagsrunde.org/Klausuren/Rechnernetze_und_Verteilte_Systeme/"},
    "Beko" : {"id" : 1020284702982144030, "link" : "https://docs.freitagsrunde.org/Klausuren/Berechenbarkeit_und_Komplexitaet/"},
    "SuS" : {"id" : 1025363108283289620, "link" : "https://docs.freitagsrunde.org/Klausuren/Signale_und_Systeme/"},
    "halbleiterbauelemente" : {"id" : 1025364581335453806, "link" : "https://docs.freitagsrunde.org/Klausuren/Halbleiterbauelemente/"}
}


def get__klausur_link(id):
    for key, value in modul_channel_data.items():
        if value["id"] == id:
            link = value["link"]
            return link
    return "Es wurden keine Altklausuren gefunden. (!altklausuren funktioniert nur in Modulchanneln)"

