# Fediseer

This service provides an REST API which can be used to retrieve various information about Fediverse instances, particularly focused on detecting and countering bad actors.

It's reliant on the [Lemmy Fediverse Observer](https://lemmy.fediverse.observer/)

The currently running instance is on https://fediseer.com

See devlog: https://dbzer0.com/blog/overseer-a-fediverse-chain-of-trust/

# Badges

You can retrieve and display a badge for your fediverse domain by requesting a .svg for it on a special endpoint

`/v1/badges/guarantees/{domain}.svg` will give you an badge of guarantee, mentioning the domains which guaranteed for your domain

E.g. ![](http://fediseer.com/api/v1/badges/guarantees/fediseer.com.svg)

`/v1/badges/endorsements/{domain}.svg` will give you an badge of endorsements, providing a count of how many other the fediverse domains guaranteed for yours

E.g ![](http://fediseer.com/api/v1/badges/endorsements/fediseer.com.svg)
