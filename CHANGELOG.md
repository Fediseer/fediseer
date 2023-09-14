# Changelog

# 0.14.1

* Fixed a bug with returning the reset API key on response

# 0.14.0

* Added pm_proxy fields which allow admins to receive PMs from the fediseer via fediseer@botsin.space

# 0.13.0

* Can now add reasons to endorsements. Likewise now the `api/v1/approvals` endoint can filter by reasons and min endorsements.

# 0.12.0

* Added hesitations, which signify mistrust against instances. A softer form of censure, to use in silencing or closer attention instead of blocking.
# 0.11.1

* Fixed censure filtering reasons using "AND" instead of "OR" as join
* Added meta reasons `__all_bigots__` and `__all_pedos__` which will attempt to filter all reasons which fall into them as supergroups

# 0.11.0

* Can now provide evidence for censures

# 0.10.0

Added `/api/v1/reports` endpoint which can show and filter recent actions on the fediseer

# 0.9.1

Added sysadmins and moderators count. This allows instance admins to self-report how many people they have in sysadmins positions and how many in moderator positions. This might be useful to find which instances might be lacking in support for their user-base.
