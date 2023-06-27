# Fediseer

This service provides an REST API which can be used to retrieve various information about Fediverse instances, particularly focused on detecting and countering bad actors.

It's reliant on the [Lemmy Fediverse Observer](https://lemmy.fediverse.observer/)

The currently running instance is on https://fediseer.com

See devlog: https://dbzer0.com/blog/overseer-a-fediverse-chain-of-trust/

# Badges

You can retrieve and display a badge for your fediverse domain by requesting a .svg for it on a special endpoint

`/v1/badges/guarantees/{domain}.svg` will give you an badge of guarantee, mentioning the domains which guaranteed for your domain

Example:
[![](http://fediseer.com/api/v1/badges/guarantees/lemmy.dbzer0.com.svg)](https://fediseer.com/api/v1/whitelist/lemmy.dbzer0.com)

`/v1/badges/endorsements/{domain}.svg` will give you an badge of endorsements, providing a count of how many other the fediverse domains guaranteed for yours

Example:
    [![](http://fediseer.com/api/v1/badges/endorsements/lemmy.dbzer0.com.svg)](https://fediseer.com/api/v1/endorsements/lemmy.dbzer0.com)
