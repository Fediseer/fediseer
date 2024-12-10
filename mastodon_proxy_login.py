import os
from mastodon import Mastodon
from dotenv import load_dotenv

load_dotenv()

Mastodon.create_app(
     'fediseer',
     api_base_url = f"https://{os.environ['MASTODON_INSTANCE']}",
     to_file = 'pytooter_clientcred.secret'
)

mastodon = Mastodon(
    version_check_mode="none",
    client_id = 'pytooter_clientcred.secret',
    access_token = f"https://{os.environ['MASTODON_TOKEN']}",
)
