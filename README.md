# Swf2HTML

Turn any `.swf` file into a single, self-contained `.html` file that works offline with 100% accuracy. You only need Python 3, an internet connection, and a .swf file to generate the .html file, nothing else.

It uses [Ruffle](https://ruffle.rs), a Flash Player emulator written in Rust and compiled to WebAssembly so keep in mind that this isn't a real .html file that you can open and direcly edit. '. `make_game.py` is the only thing needed, it builds the player and embeds your game in one step.

## Use

As stated earlier, you need Python 3 for this to work, to generate it you run the following commands;

```
python3 make_game.py game.swf              # writes game.html next to game.swf
python3 make_game.py a.swf b.swf           # writes a.html and b.html
python3 make_game.py game.swf -o out.html --title "My Game" --open
```
If you are on windows you can drag your .swf file on top of the make_game.py file to generate it instead.

Copy the generated `.html` anywhere and open it in a browser; it needs nothing else.

The first run downloads the official Ruffle package from npm (about 20 MB, checked against a pinned checksum) and caches the built player in `~/.cache/swf2html/`. Later runs need no internet. To build offline, download the tarball named in `make_game.py` and pass it with `--ruffle FILE.tgz`.

A text file containing the base64 of a `.swf` is also accepted as input.

## Behaviour

- When you start, there is no gui but what is in the actual flash game.
- It starts automatically but because of how browsers work sound only begins after your first click or tap.
- Anything that loads files from the internet will not work offline.


## Compatibility

Any browser with WebAssembly should work, yours probably does but if you have a nieche browser it might be smart to check first. Ruffle handles most ActionScript 1/2 content and a growing share of ActionScript 3, so some games may have glitches.

Generated files are about 14 MB plus the size of your game (the engine is stored deflate-compressed and base64-encoded, with a small built-in decompressor for browsers that lack native support).

## How the player is built

`make_game.py` unpacks Ruffle's self-hosted npm package (`@ruffle-rs/ruffle` 0.6.0), compresses the two WebAssembly binaries, and inlines everything into one HTML page. The JavaScript chunks are pre-registered so no files are fetched at runtime, and a small `fetch` shim serves the embedded WebAssembly. Ruffle's license is included inside each generated file.

## Licenses

The scripts in this repository are under the MIT license (see `LICENSE`). Ruffle is dual-licensed MIT or Apache-2.0.

Only convert Flash content you have the right to use. Do not commit copyrighted games or the HTML files generated from them to this repository.
