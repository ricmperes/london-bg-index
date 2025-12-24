# London BG Index

🎲 **Welcome to the London Boardgame Index GitHub page!** 🎲

This repository hold the pages of https://ricmperes.github.io/london-bg-index/ and scripts to generate the ratings page. The website is static but can be regenerated to hold updated ratings.

To fetch the BGG ratings, access to the [BGG XML API](https://boardgamegeek.com/using_the_xml_api) is required. An application to get an access tokan can be done [here](https://boardgamegeek.com/applications).

## Running a local instance

Get a BGG XML API key at https://boardgamegeek.com/applications and register it as `BGG_token`:
```bash
cd ~
echo 'export BGG_token="your_token_here"' >> ~/.bashrc
source .bashrc
```

Clone the repo:
```bash
git clone git@github.com:ricmperes/london-bg-index.git
cd london-bg-index
```

Add your table of games to inputs and adapt `fetch_bgg_data.py` accordingly.

Generate the ratings table page:
```bash
cd scripts
python fetch_bgg_data.py --n-processes 1
python make_table.py
```
> In principle it could be executed in parallel with the flag `n-processes` but somehow it makes it impossible to fetch the right data from the BGG XML API, probably from requesting and reading several HTML messages at the same time. To fix? Maybe.


That's it! **Although**... some games will likely fail to be found in the BGG API or get confused. For now these need to be fixed *by hand*. Change the BGG_ID to the correct one and run:
```bash
python fetch_bgg_data.py --recompile
```
If the initally pulled ratings were put in a different file, change the name after the parameter. Thi scommand can also be used to update the ratings to the current ones in BGG.


## Contributing

 Checkout the [About page](https://ricmperes.github.io/london-bg-index/pages/about.html) for the established development roadmap!

To report a bug or feature request, please use the [issue tracker](https://github.com/ricmperes/london-bg-index/issues). Feel free to propose changes via a [PR](https://github.com/ricmperes/london-bg-index/pulls)!