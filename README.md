# ACT RESPONSIBLY

These scripts enable you to revert edits done by other people. Never do this unless you are
absolutely sure that the edit in question is either malicious or accidental. Make an effort to talk
to the user beforehand and afterwards.  Always be kind to other mappers, and always assume that if
they did something wrong it must have been an error, a misunderstanding, or their cat chasing fluff
across the keyboard!

When in doubt, discuss things on the [mailing list](https://lists.openstreetmap.org/) before you act.
Also, read the wiki article on
[automated edits](https://wiki.openstreetmap.org/wiki/Automated_Edits) and the [Automated Edits
Code of Conduct](https://wiki.openstreetmap.org/wiki/Automated_Edits_code_of_conduct).

These scripts do not have safety nets. Be sure that you feel confident to fix anything you might
break. If you do not know your PUTs from your GETs, if you do not know the details of API 0.6, or
know what changesets are and how they work, then DO NOT USE THIS SOFTWARE.

With power comes responsibility. By using this tool you are responsible for all your mistakes.
Flexibility is a design goal of this tool. You might have to write your own revert logic in order to
do a revert. PLEASE USE THE DEVELOPMENT API (commonly referred as *OpenStreetMap Dev API*) FOR ALL
YOUR TESTS.  Please also take the time and WRITE UNIT TESTS before you run your code against the
production API.


# Machina Reparanda

Machina Reparanda is a flexible Python 3.x framework to revert changesets. In difference to existing
revert tools, it can also be used to revert only certain parts of the changes of a user.

For example, if a user systematically changed the language of name tags and did a lot of other
edits, you can just revert the tag changes but keep all other contributions. Flexibility is the
design goal of this framework. This means that you can decide what will be reverted and how
conflicts will be solved if the object has been changed after the changset(s) to be reverted. Your
decisions are manifested in Python code, i.e. you have to implement the rules, Machina Reparanda
should follow. Please test your code. Write unit tests!

## Dependencies

* Python3
* [Pyosmium](http://osmcode.org/pyosmium/) (Python bindings for the Osmium 2.x C++ library)
* [Requests](http://docs.python-requests.org/en/master/)

Debian: `python3-pyosmium python3-requests`

Arch Linux: `python-requests` and from AUR `pyosmium-git`

## How to use

1. Look into the `implementations/` directory to check if there is already a implementation (you
   could also call it "strategy") for the type of revert you want to do. If yes, jump to step 5.
2. Create a new Python file in `implemenations/`, e.g. `implementations/clever_revert.py`. It
   contains a class called `RevertImplementation` which is derived from
   `AbstractRevertImplementation`.
3. `RevertImplementation` should implement following callback methods:

   * `handle_obj` takes an instance of `osmium.osm.MutableOSMObject` as argument: This method handles
    objects which have only been edited once by all the changesets to be reverted. The object has
    to be edited or deleted by these changesets but not created.
   * `handle_v1_obj` takes an instance of `osmium.osm.MutableOSMObject` as argument: This method
    handles objects which have been created and not modified by the changesets to be reverted.
   * `handle_multiple_versions` takes a list of `osmium.osm.MutableOSMObject` as argument: This
    method handles objects which have been edited multiple times by the changesets to be reverted.
    This means, the user(s) uploaded more than one version.

   All these versions should return an instance of `osmium.osm.MutableOSMObject` and a set of
   changeset IDs (integers) whose changes have been reverted fully or partially. If no action is
   necessary, they should return `None, None`.
4. Write unit tests for your implementation and run them. The `test/` directory contains examples.
   Run `make test` to run all unit tests or `python3 -m unittest tests/TESTNAME.py` for a single
   test.
5. Write a configuration file, set the correct API base URL and enter your account credentials in
   a JOSN file which looks like `sample-config.json`. If you don't save your password in the file
   you will be asked to enter it on the command line.
6. Download the OSC files of the changesets you want to revert. You might use
   [download_changesets.sh](https://github.com/woodpeck/osm-revert-scripts/blob/master/download_changesets.sh)
   by Frederik Ramm. It will save them as files named `c<changeset_id>.osc`.
7. Run `python3 revert_tag_changes.py -c CONFIG_FILE -i IMPLEMENTATION_FILE --dryrun "changeset
   comment" path/to/c*.osc`


## License

This program is published under the terms of GNU General Public License version 2 or newer. See
[LICENSE.txt](LICENSE.txt) for the full legal code of GNU General Public License version 3.
