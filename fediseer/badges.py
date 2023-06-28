from pybadges import badge
from loguru import logger
import base64

with open('fediseer/assets/crossed-chains.svg', 'rb') as file:
    svg_data = file.read()
    base64_data = base64.b64encode(svg_data).decode('utf-8')
    embed_guarantee = f"data:image/svg+xml;base64,{base64_data}"    
with open('fediseer/assets/thumb-up.svg', 'rb') as file:
    svg_data = file.read()
    base64_data = base64.b64encode(svg_data).decode('utf-8')
    embed_endorsement = f"data:image/svg+xml;base64,{base64_data}"    

def generate_guarantee_badge(domain: str, guarantor: str):
    left_color = "DarkSlateGray "
    right_color = "DarkOliveGreen"
    right_text=guarantor
    if guarantor is None:
        right_color = "DarkRed"
        right_text="None"
    guarantee_badge = badge(
        left_text="Guarantor", 
        right_text=right_text, 
        left_color=left_color,
        right_color=right_color,
        logo=embed_guarantee,
        whole_title="Fediseer Guarantee",
        left_title=domain,
        right_title="Guarantor",
        left_link="https://fediseer.com",
        right_link=f"https://fediseer.com/api/v1/endorsements/{domain}",
    )
    return guarantee_badge

def generate_endorsements_badge(domain: str, count: int):
    left_color = "DarkSlateGray "
    right_color = "DarkOliveGreen"
    right_text=str(count)
    if count == 0:
        right_color = "DarkRed"
    endorsements_badge = badge(
        left_text="Endorsements", 
        right_text=right_text, 
        left_color=left_color,
        right_color=right_color,
        logo=embed_endorsement,
        whole_title="Fediseer Endorsements",
        left_title=domain,
        right_title="Endorsements Count",
        left_link="https://fediseer.com",
        right_link=f"https://fediseer.com/api/v1/whitelist/{domain}",
    )
    return endorsements_badge
