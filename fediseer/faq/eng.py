from fediseer.consts import MAX_TAGS

ENG_HEADER = """#Fediseer FAQ

This document will attempt to provide some definitions and answers to common questions around the fediseer.

[TOC]
"""

ENG_TRANSLATION_MESSAGE = "**Attention**: This translation is not completed yet."


ENG_FAQ = [
    {
        "category": "terminology",
        "category_translated": "terminology",
        "translated": True,
        "added": "2023-09-25",
        "question": "What is the Fediseer?",
        "stub": "fediseer",
        "document": 
"""The fediseer is a service for the fediverse which attempts to provide a crowdsourced human-curated spam/ham classification of fediverse instances as well as provide a public space to specify approval/disapproval of other instances.

In simple terms, using the fediseer, we attempt to figure out if an instance is spam or not through a human-driven system called the "chain of trust".

The three main concepts used in Fediseer are guarantees, endorsements and censures.

The fediseer provides a machine readable API to consume the data contained within.
"""
    },
    {
        "category": "terminology",
        "category_translated": "terminology",
        "translated": True,
        "added": "2023-09-25",
        "question": "What is a guarantee?",
        "stub": "guarantee",
        "document": 
"""Basically, any guaranteed instance is known as definitelly "not spam" (AKA "ham"). That doesn't mean any non-guaranteed instance is spam. Rather it is considered "unknown". The only reasoning to guarantee an instance is whether they are spam or not. The objective here being to prevent malicious actors from spawning an infinite amount of new instances on the fediverse to send spam.

Each instance can only be guaranteed by one instance and guarantee another instance. This is called the "chain of trust"

Guarantees are community driven. While the fediseer can guarantee at the top level as well, we hope that instance admins will guarantee the instances they know of and help ensure the health of the network.
"""
    },
    {
        "category": "terminology",
        "category_translated": "terminology",
        "translated": True,
        "added": "2023-09-25",
        "question": "What is the chain of trust?",
        "stub": "chain of trust",
        "document": 
"""Because each instance on the fediseer can guarantee and be guaranteed by a single instance, this causes a chain to form starting from the fediseer itself. Any instance guaranteed by such an unbroken chain is considered as ham. If the guarantee for any instance in this chain is revoked, the chain of trust is broken and any instances below are considered not-guaranteed.

This allows the fediseer to quickly deal with spam instances that sneaked into the fediseer and then guaranteed a bunch more of the spammy friends. As the chain can be revoked higher up, even a whole spam network can be countered by revoking the guarantee from the first spammer guaranteed.

[Chain of Trust Devlog](https://dbzer0.com/blog/overseer-a-fediverse-chain-of-trust/)
"""
    },
    {
        "category": "terminology",
        "category_translated": "terminology",
        "translated": True,
        "added": "2023-09-25",
        "question": "What is an endorsement?",
        "stub": "endorsement",
        "document": 
"""An endorsement is a completely subjective positive judgement from one instance to another. Effectively signifying that instance A "approves" of instance B. The reason for this can be anything and do not have to be stated.

An instance can be approve of any number of instances and be endorsed by any number of instances. One can even get an autogenerated badge with the amount of endorsements they've received to display.

When looking at the instance whitelist, one can also filter by amount of endorsements. Likewise one can also export the list of instances endorsed by a subset of instances.
"""
    },
    {
        "category": "terminology",
        "category_translated": "terminology",
        "translated": True,
        "added": "2023-09-25",
        "question": "What is a censure?",
        "stub": "censure",
        "document": 
"""An censure is a completely subjective negative judgement from one instance to another. Effectively signifying that instance A "disapproves" of instance B. The reason for this can be anything and do not have to be stated.

An instance can be censure any number of instances and be censured by any number of instances.

One can export the list of instances censured by a subset of instances.
"""
    },
    {
        "category": "terminology",
        "category_translated": "terminology",
        "translated": True,
        "added": "2023-09-25",
        "question": "What is a hesitation?",
        "stub": "hesitation",
        "document": 
"""An hesitation is a mulder version of a censure, it signifies some sort of mistrust of one instance towards another. The reason for this can be anything and do not have to be stated.

An instance can be hesitate against number of instances and be doubted by number of instances.

One can export the list of instances hesitate by a subset of instances.
"""
    },
    {
        "category": "terminology",
        "category_translated": "terminology",
        "translated": True,
        "added": "2023-09-25",
        "question": "What is an instance claim?",
        "stub": "claim",
        "document": 
"""A claimed instance is an instance whose admin has requisted an API key with which to use the fediseer as their instance.

Fediseer has no users. Instead it's driven by instance admins only. Instance admins likewise only act as their instances.
"""
    },
    {
        "category": "terminology",
        "category_translated": "terminology",
        "translated": True,
        "added": "2023-09-25",
        "question": "What are instance visibilities?",
        "stub": "visibilities",
        "document": 
"""An instance can set the visibility of its endorsements, censures, and/or hesitations to one of the following:

* `OPEN`: Anyone can see and retrieve that list
* `ENDORSED`: Only instances endorsed by the source instance, can see that list
* `PRIVATE`: Only the source instance can see that list.

Note that guarantees are always public as this is necessary for the good functioning of the chain of trust.
"""
    },
    {
        "category": "terminology",
        "category_translated": "terminology",
        "translated": True,
        "added": "2023-09-25",
        "question": "What is an instance flag?",
        "stub": "flag",
        "document": 
"""An instance flag represents some marking from the fediverse admins toward an instance. There's currently the following flags

* `RESTRICTED`: The instance cannot guarantee, endorse, censure or hesitate other instances anymore. This flag is only used against egregious trolling or malicious behaviour.
* `MUTED`: The instance's visibilities are forcefully set to `PRIVATE` and cannot be changed. This flag is meant to used against trolling or harassing behaviour.
"""
    },
    {
        "category": "terminology",
        "category_translated": "terminology",
        "translated": True,
        "added": "2023-09-27",
        "question": "What is an instance tag?",
        "stub": "tag",
        "document": 
f"""An instance tag is up to {MAX_TAGS} voluntary classifications by the instance admins for their own instance. 
These tags can be anything that the owner wishes to use to describe their instance in a few words.

The tags can then be used by integrators to filter instances for their block or allow lists, 
or to help people discover instances relevant to their interests.

Like always, no hate speech is allowed.
"""
    },
    {
        "category": "functionality",
        "category_translated": "functionality",
        "translated": True,
        "added": "2023-09-25",
        "question": "How can I claim my instance?",
        "stub": "instance claim",
        "document": 
"""You can either use the rest API we have provided, providing your instance domain and admin username on it. Alternativey you can use one of our frontends.

You will then receive an API key in PMs, which you can afterwards use to represent your instance on the fediseer.
"""
    },
    {
        "category": "functionality",
        "category_translated": "functionality",
        "translated": True,
        "added": "2023-09-25",
        "question": "What can I write in my reasons for endorsements, hesitations and censures?",
        "stub": "reasons",
        "document": 
"""This is an optional free-form field for up to 255 characters. If will be handled as a comma-separated list, so we suggest using commas to split your reasons. As the reasons are meant to be used for filtering by others, we suggest you limit each entry to 2-5 words.

You are not allowed to use hate speech in your reasons.
"""
    },
    {
        "category": "functionality",
        "category_translated": "functionality",
        "translated": True,
        "added": "2023-09-25",
        "question": "What can I write in my evidence for censures and hesitations?",
        "stub": "evidence",
        "document": 
"""This is an optional free-form field you can use to provide receipts for this judgement or explain your reasoning in depth. If you want to provide screenshots, we suggest linking to them, for example by [opening a thread in fediblock](https://lemmy.dbzer0.com/c/fediblock).

You are not allowed to use hate speech in your evidence.
"""
    },
    {
        "category": "philosophy",
        "category_translated": "philosophy",
        "translated": True,
        "added": "2023-09-25",
        "question": "Doesn't this all cause fediverse centralization?",
        "stub": "centralization",
        "document": 
"""No. The fediseer has no official integration with fediverse software. The fediseer simply provides the information within in a machine-readable REST API. How this information is utilized is up to the various instance admins. One is perfectly free to not utilize the fediseer whatsoever.

Not only that, but the fediseer is free and open source software, allowing anyone to re-host it and run it according to their own principles. If you do not trust this fediseer instance, you can rehost yourself and people can switch instances by changing a domain name.
"""
    },
    {
        "category": "philosophy",
        "category_translated": "philosophy",
        "translated": True,
        "added": "2023-09-25",
        "question": "Doesn't this make the fediseer an authority on the fediverse?",
        "stub": "authority",
        "document": 
"""The fediseer is designed to be completely crowd-sourced as pertains to the chain of trust. The admin of the fediseer does not control what people guarantee, endorse or censure. The various instance admins are driving the chain of trust.
"""
    },
]