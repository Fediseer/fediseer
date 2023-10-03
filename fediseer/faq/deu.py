from fediseer.consts import MAX_TAGS

DEU_HEADER = """#Fediseer FAQ

In diesem Dokument wird versucht, einige Definitionen und Antworten auf allgemeine Fragen rund um den Fediseer zu geben.

[TOC]
"""

DEU_TRANSLATION_MESSAGE = "**Achtung**: Diese Übersetzung ist noch nicht abgeschlossen."


DEU_FAQ = [
    {
        "category": "terminology",
        "category_translated": "Terminologie",
        "translated": True,
        "added": "2023-09-25",
        "question": "Was ist Fediseer?",
        "stub": "fediseer",
        "document":
"""Fediseer ist ein Dienst für das Fediverse, der versucht, eine von Menschenhand kuratierte Vertrauens-Klassifizierung von Fediverse-Instanzen bereitzustellen sowie einen öffentlichen Raum zu bieten, um die Zustimmung/Ablehnung anderer Instanzen anzugeben.

Vereinfacht ausgedrückt, versuchen wir mit dem Fediseer herauszufinden, ob eine Instanz Vertrauenswürdig ist oder nicht, und zwar mit Hilfe eines menschengesteuerten Systems, der sogenannten "Vertrauenskette".

Die drei Hauptfunktionen sind dabei: Empfehlungen, Bürgschaften und Tadel.

Der Fediseer bietet eine maschinenlesbare API, um die darin enthaltenen Daten zu nutzen.
"""
    },
    {
        "category": "terminology",
        "category_translated": "Terminologie",
        "translated": True,
        "added": "2023-09-25",
        "question": "Was ist eine Bürgschaft?",
        "stub": "guarantee",
        "document":
""" Jede Instanz mit einer Bürgschaft kann als vertrauenswürdig angesehen werden. Das bedeutet nicht, dass eine Instanz ohne Bürgschaft nicht Vertrauenswürdig ist. Es bedeutet vielmehr, dass der Status "unbekannt" ist. Der Zweck der Bürgschaft für eine Instanz besteht darin, andere wissen zu lassen, ob es sich um eine vertrauenswürdige Instanz handelt. Damit soll verhindert werden, dass böswillige Akteure eine unendliche Anzahl neuer Instanzen im Fediverse erzeugen, um Spam zu versenden.

Jede Instanz kann durch eine andere Instanz eine Bürgschaft erhalten und kann dann für 20 andere Instanzen bürgen. Dies wird als "Vertrauenskette" bezeichnet.

Bürgschaften sind von der Gemeinschaft abhängig. Während der Fediseer auch auf der obersten Ebene Bürgschaften vergeben kann, hoffen wir, dass die Instanz-Admins für die Instanzen bürgen, von denen sie wissen, dass sie vertrauenswürdig sind.
"""
    },
    {
        "category": "terminology",
        "category_translated": "Terminologie",
        "translated": True,
        "added": "2023-09-25",
        "question": "Was ist die Vertrauenskette?",
        "stub": "chain of trust",
        "document":
""" Da jede Instanz auf dem Fediseer für andere Instanzen bürgt und eine Bürgschaft erhalten kann, bildet sich eine Kette, die vom Fediseer selbst ausgeht. Jede Instanz, die von einer solchen ununterbrochenen Kette eine Bürgschaft besitzt, gilt als vertrauenswürdig. Wenn die Bürgschaft für eine Instanz aufgehoben wird, wird die Vertrauenskette unterbrochen und alle darunterliegenden Instanzen werden als bürgschaftslos betrachtet.

Das hilft Fediseer, schnell mit unvertrauenswürdigen Instanzen fertig zu werden, die sich in Fediseer eingeschlichen haben und dann für weitere unvertrauenswürdige Instanzen bürgen. So kann z.B. ein ganzes Spam-Netzwerk bekämpft werden, indem die Bürgschaft des ersten Spammers widerrufen wird.

[Chain of Trust Devlog](https://dbzer0.com/blog/overseer-a-Fediverse-chain-of-trust/)
"""
    },
    {
        "category": "terminology",
        "category_translated": "Terminologie",
        "translated": True,
        "added": "2023-09-25",
        "question": "Was ist eine Empfehlung?",
        "stub": "endorsement",
        "document":
""" Eine Empfehlung ist ein völlig subjektives positives Urteil von einer Instanz gegenüber einer anderen. Es bedeutet, dass Instanz A Instanz B vertraut. Dafür kann es vielerlei Gründe geben, welche auch angegeben werden können.

Eine Instanz kann beliebig viele Instanzen Empfehlungen aussprechen und beliebig viele Empfehlungen erhalten. Es gibt ein Abzeichen, das die Anzahl der Empfehlungen anzeigt. Sie können das Abzeichen im linken Menü unter Ihrem Instanznamen sehen.

Wenn man sich die Whitelist der Instanzen ansieht, kann man auch nach der Anzahl der Empfehlungen filtern. Ebenso kann man die Liste der Instanzen, die von einer Teilmenge von Instanzen empfohlen werden, exportieren.
"""
    },
    {
        "category": "terminology",
        "category_translated": "Terminologie",
        "translated": True,
        "added": "2023-09-25",
        "question": "Was ist ein Tadel?",
        "stub": "censure",
        "document":
"""Ein Tadel ist ein völlig subjektives negatives Urteil von einer Instanz zur anderen. Es bedeutet, dass die Instanz A die Instanz B "missbilligt". Der Grund dafür kann alles sein und muss nicht angegeben werden.

Eine Instanz kann von einer beliebigen Anzahl von Instanzen getadelt werden und von einer beliebigen Anzahl von Instanzen getadelt werden.

Man kann die Liste der Instanzen, die von einer Teilmenge von Instanzen zensiert werden, exportieren.
"""
    },
    {
        "category": "terminology",
        "category_translated": "Terminologie",
        "translated": True,
        "added": "2023-09-25",
        "question": "Was ist ein Zweifel?",
        "stub": "hesitation",
        "document":
"""  Ein Zweifel gleicht einem Tadel, nur nicht so streng. Man könnte es als missfallen und nicht als unvertrauenswürdig einstufen.

Eine Instanz kann beliebig viele Instanzen tadeln sowie von beliebig vielen getadelt werden. Auch hierfür kann es vielerlei Gründe geben, welche ebenfalls angegeben werden können.

Man kann die Liste der Instanzen, die von einer Teilmenge von Instanzen angezweifelt werden, exportieren.
"""
    },
    {
        "category": "terminology",
        "category_translated": "Terminologie",
        "translated": True,
        "added": "2023-09-25",
        "question": "Was bedeutet es eine Instanz zu beanspruchen?",
        "stub": "claim",
        "document":
""" Eine beanspruchte Instanz ist eine Instanz, deren Administrator einen API-Schlüssel von Fediseer angefordert hat.

Fediseer hat keine Benutzerkonten. Stattdessen wird es nur von Instanzadministratoren betrieben welche ausschließlich als ihre Instanz agieren.
"""
    },
    {
        "category": "terminology",
        "category_translated": "Terminologie",
        "translated": True,
        "added": "2023-09-25",
        "question": "Was sind Sichtbarkeiten von Instanzen?",
        "stub": "visibilities",
        "document":
"""Eine Instanz kann die Sichtbarkeit ihrer Vermerke, Rügen und/oder Vorbehalte auf eine der folgenden Möglichkeiten einstellen:
* `OPEN`: Jeder kann diese Liste sehen und abrufen
* `ENDORSED`: Nur Instanzen, die von der Quellinstanz gebilligt wurden, können diese Liste sehen
* `PRIVATE`: Nur die Quellinstanz kann diese Liste sehen.

Beachten Sie, dass Garantien immer öffentlich sind, da dies für das gute Funktionieren der Vertrauenskette notwendig ist.
"""
    },
    {
        "category": "terminology",
        "category_translated": "Terminologie",
        "translated": True,
        "added": "2023-09-25",
        "question": "Was ist ein Instanzkennzeichen?",
        "stub": "flag",
        "document":
"""Eine Instanzkennzeichnung stellt eine Markierung der Fediverse-Administratoren für eine Instanz dar. Derzeit gibt es die folgenden Flaggen

* `EINGESCHRÄNKT`: Die Instanz kann nicht mehr für andere Instanzen garantieren, sie unterstützen, tadeln oder zögern. Diese Flagge wird nur gegen ungeheuerliches Trolling oder bösartiges Verhalten verwendet.
* `Stummgeschaltet`: Die Sichtbarkeit der Instanz wird zwangsweise auf `PRIVATE` gesetzt und kann nicht geändert werden. Dieses Flag ist gegen Trolling oder schikanöses Verhalten gedacht.
"""
    },
    {
        "category": "terminology",
        "category_translated": "Terminologie",
        "translated": True,
        "added": "2023-09-27",
        "question": "Was ist ein Instanz-Tag?",
        "stub": "tag",
        "document":
f"""Ein Instanz-Tag besteht aus bis zu {MAX_TAGS} freiwilligen Klassifizierungen durch die Instanzadministratoren für ihre eigene Instanz.
Diese Tags können alles sein, was der Eigentümer verwenden möchte, um seine Instanz in wenigen Worten zu beschreiben.

Die Tags können dann von Betreibern verwendet werden, um Instanzen für ihre Sperr- oder Erlaubnislisten zu filtern,
oder um Menschen zu helfen, Instanzen zu finden, die ihren Interessen entsprechen.

Wie immer ist keine Hassrede erlaubt.
"""
    },
    {
        "category": "functionality",
        "category_translated": "Funktionalität",
        "translated": True,
        "added": "2023-09-25",
        "question": "Wie kann ich meine Instanz beanspruchen?",
        "stub": "instance claim",
        "document":
"""Sie können entweder die von uns bereitgestellte Rest-API verwenden, indem Sie Ihre Instanzdomäne und Ihren Administrator-Benutzernamen angeben. Alternativ können Sie auch unseren [Frontend](https://gui.fediseer.com/) verwenden.

Sie erhalten dann einen API-Schlüssel als PN, den Sie anschließend verwenden können, um Ihre Instanz auf dem Fediseer zu repräsentieren.
"""
    },
    {
        "category": "functionality",
        "category_translated": "Funktionalität",
        "translated": True,
        "added": "2023-09-25",
        "question": "Was kann ich in meine Begründungen für Befürwortungen, Bedenken und Tadel schreiben?",
        "stub": "reasons",
        "document":
"""Dies ist ein optionales Textfeld das bis zu 255 Zeichen erlaubt. Es wird als kommagetrennte Liste behandelt, daher empfehlen wir Ihnen, Ihre Gründe durch Kommas zu trennen. Da die Gründe dazu dienen sollen, von anderen gefiltert zu werden, empfehlen wir Ihnen, jeden Eintrag auf 2-5 Wörter zu beschränken.

Sie dürfen in Ihren Begründungen keine Hassreden verwenden.
"""
    },
    {
        "category": "functionality",
        "category_translated": "Funktionalität",
        "translated": True,
        "added": "2023-09-25",
        "question": "Was kann ich als Begründung für meine Zweifel schreiben?",
        "stub": "evidence",
        "document":
"""Dies ist ein optionales Textfeld, das Sie nutzen können, um Belege für dieses Aktion zu liefern oder Ihre Argumentation ausführlich zu erläutern. Wenn Sie Screenshots zur Verfügung stellen möchten, empfehlen wir Ihnen, diese zu verlinken, z. B. durch [Eröffnung eines Threads im Fediblock] (https://lemmy.dbzer0.com/c/fediblock).

Sie dürfen in Ihren Belegen keine Hassrede verwenden.
"""
    },
    {
        "category": "philosophy",
        "category_translated": "Philosophie",
        "translated": True,
        "added": "2023-09-25",
        "question": "Führt das alles nicht zu einer Zentralisierung der Föderation?",
        "stub": "centralization",
        "document":
"""Nein. Der fediseer hat keine offizielle Integration mit Fediverse Software. Der fediseer stellt lediglich die darin enthaltenen Informationen in einer maschinenlesbaren REST API zur Verfügung. Wie diese Informationen genutzt werden, bleibt den verschiedenen Instanzadministratoren überlassen. Es steht ihnen völlig frei, den fediseer überhaupt nicht zu nutzen.


Nicht nur das, der Fediseer ist eine freie und quelloffene Software, die es jedem erlaubt, sie neu zu hosten und nach seinen eigenen Prinzipien zu betreiben. Wenn Sie dieser fediseer-Instanz nicht trauen, können Sie sich selbst neu hosten und die Leute können die Instanz wechseln, indem sie einen Domainnamen ändern.
"""
    },
    {
        "category": "philosophy",
        "category_translated": "Philosophie",
        "translated": True,
        "added": "2023-09-25",
        "question": "Macht dies den Fediseer nicht zu einer Autorität im Fediversum?",
        "stub": "authority",
        "document":
"""Der Fediseer ist so konzipiert, dass die Vertrauenskette vollständig von der Masse getragen wird. Der Administrator des Fediseers hat keine Kontrolle darüber, was die Leute garantieren, gutheißen oder zensieren. Die verschiedenen Instanzadministratoren steuern die Vertrauenskette.
"""
    },
]