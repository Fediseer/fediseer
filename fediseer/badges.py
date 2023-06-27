from pybadges import badge
from loguru import logger

def generate_guarantee_badge(domain: str, guarantor: str):
    left_color = "green"
    right_text=guarantor
    if guarantor is None:
        left_color = "red"
        right_text="None"
    guarantee_badge = badge(
        left_text="Guarantee", 
        right_text=right_text, 
        left_color=left_color,
        logo="https://badges.fediseer.com/fediseer_logo_sm.png",
        whole_title="Fediseer Guarantee",
        left_title=domain,
        right_title="Guarantor",
        left_link="https://fediseer.com",
        right_link=f"https://fediseer.com/api/v1/whitelist/{domain}",
    )
    return guarantee_badge

def generate_endorsements_badge(domain: str, count: int):
    left_color = "LimeGreen"
    right_text=str(count)
    if count == 0:
        left_color = "red"
    endorsements_badge = badge(
        left_text="Endorsements", 
        right_text=right_text, 
        left_color=left_color,
        logo="https://badges.fediseer.com/fediseer_logo_sm.png",
        whole_title="Fediseer Endorsements",
        left_title=domain,
        right_title="Endorsements Count",
        left_link="https://fediseer.com",
        right_link=f"https://fediseer.com/api/v1/whitelist/{domain}",
    )
    return endorsements_badge
