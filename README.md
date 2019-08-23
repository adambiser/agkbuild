# agkbuild

## What is agkbuild?

Agkbuild is a Python script to automate building and exporting AppGameKit Classic Tier 1 projects.
Sometimes write once, run anywhere doesn't quite cut it and as you develop your game, you might end up having a full version, a demo, a Steam release, Android releases on Google Play and Amazon, etc. all needing to be built from the same code base.

This script allows you to swap #include/#insert files depending on what's being built, set the APK package name, and more.

## Requirements

You must own [AppGameKit Classic](https://www.appgamekit.com/) to use this.
This script will not work with the new AppGameKit Studio because it does not have a sepectate compiler application (AGKCompiler.exe).

You will also need [Python 3.7+](https://www.python.org/) to run the script.

## Installing

Before getting started, you'll need to install the script requirements using

```pip install -r requirements.txt```

## Issues?

Use the [issue tracker](https://github.com/adambiser/agkbuild/issues).

## License

This project is licensed under the [GPL-2.0 License](COPYING) to match [the AppGameKit IDE](https://github.com/TheGameCreators/AGKIDE) from which some of this code was ported.

## Acknowledgments

* TheGameCreators for making AppGameKit.
