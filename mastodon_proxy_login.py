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
    client_id = 'pytooter_clientcred.secret',
    api_base_url = f"https://{os.environ['MASTODON_INSTANCE']}"
)
mastodon.log_in(
    os.environ['MASTODON_EMAIL'],
    os.environ['MASTODON_PASSWORD'],
    to_file = 'pytooter_usercred.secret'
)
