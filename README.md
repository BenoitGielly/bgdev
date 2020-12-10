# Introduction

`bgdev` is a custom suite of python tools and utility function, mostly created for Autodesk Maya and focusing on TD roles like Character Rigging or Animation.
It started with my career back in August 2013, and has grown over time with the experience I got from various jobs in different companies.

## License

The current repository is under [MIT License](LICENSE).

Feel free to use, change, and share it as you please.
You don't have to, but mentioning my name whenever you use source code from here would be much appreciated!

## API Documentation

You can find a generated sphinx documentation at <https://bgdev.readthedocs.io/en/latest/>

# Installation

`bgdev` doesn't require anything apart from a working version of Autodesk Maya.
You will find a module file available in `bgdev\src\apps-maya\module\modules\` which you can add to the `MAYA_MODULE_PATH` environment variable.
It'll allow Maya to pick up the whole repo automatically for you on startup.

You can always run multiple `sys.path.append()` on the various Python source folders: `bgdev\src\apps-maya\python` and `bgdev\src\apps-python`.
Don't forget to include the Python external libraries in `bgdev\src\site-packages\Python27` too or some tools may not be working!

# Usage

Once the module is installed, all you need to do is to run `import bgdev` inside Maya.
_(Obviously you need to call the right tool/library, but if you found this repo you probably know how python works! :-))_
