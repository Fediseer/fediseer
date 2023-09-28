# Help us translate the fediseer FAQ

We wish to allow the Fediseer [FAQ](/faq) to be available to multiple languages and for that we need your help.

If you want to translate, you can do it two ways:


## Pull Request

Use this approach if you're good with github and/or git. If not, see the `Simple` approach below

Go to our github repository (https://github.com/Fediseer/fediseer) and create a pull request for the language you would like to contribute.

All you need to do is make a copy [of the english version](https://github.com/Fediseer/fediseer/blob/main/fediseer/faq/eng.py) into the [3-letter ISO 639-3 code](https://iso639-3.sil.org/code_tables/639/data) of the language you wish to translate to. 

For example if you would like to translate into arabic, you would create a file `fediseer/faq/ara.py`.

Then rename all variables of "ENG" to your language code. To follow our example, you would rename `ENG_HEADER` to `ARA_HEADER` before translating its contents.

**Note:** Do not translate the `category` key. Only the `category_translated` key. 

Once you're done with a field, change its `translated` key to `True`

Finally in https://github.com/Fediseer/fediseer/blob/main/fediseer/faq/__init__.py, follow the other existing language as examples, and import and add the entries for your new language code.

## Simple

Use this approach if you don't understand github or git well.

Simply [download the english version](https://github.com/Fediseer/fediseer/blob/main/fediseer/faq/eng.py)

Edit it as best as you can with your text editor, then [open a new issue with your results](https://github.com/Fediseer/fediseer/issues) and post it there. We'll handle the rest. You can send us partial translations if you want and work on them slowly.

