from .eng import ENG_FAQ, ENG_HEADER, ENG_TRANSLATION_MESSAGE
from .ell import ELL_FAQ, ELL_HEADER, ELL_TRANSLATION_MESSAGE
from .deu import DEU_FAQ, DEU_HEADER, DEU_TRANSLATION_MESSAGE

LANGUAGE_NAMES = {
    "eng": "English",
    "ell": "Ελληνικά",
    "deu": "Deutsch",
}

FAQ_LANGUAGES = {
    "eng": ENG_FAQ,
    "ell": ELL_FAQ,
    "deu": DEU_FAQ,
}

HEADER_LANGUAGES = {
    "eng": ENG_HEADER,
    "ell": ELL_HEADER,
    "deu": DEU_HEADER,
}

TRANSLATION_MESSAGE_LANGUAGES = {
    "eng": ENG_TRANSLATION_MESSAGE,
    "ell": ELL_TRANSLATION_MESSAGE,
    "deu": DEU_TRANSLATION_MESSAGE,
}