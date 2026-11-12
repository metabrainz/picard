# Command engine and shell

> STATUS: **experimental.** `picard-cli shell` is a console over a command
> engine that drives Picard without its GUI: it adds files, clusters them,
> looks them up on MusicBrainz, shows and saves their tags. Part of this
> document describes what exists (the first sections); the "Roadmap" at the end
> is the design it is meant to grow into, and is not implemented.

## Overview

A command engine runs a vocabulary of commands (`file add`, `cluster`, `lookup`,
`metadata show`, `save`, ...) against the working set of Picard, the same
`Workspace` that the GUI uses. The commands are written once and return
structured results; a frontend (today the interactive console, `picard-cli
shell`) reads a line, runs the command, and renders the result.

```text
$ picard-cli shell
picard> file add ~/Music/incoming/*.flac
picard> cluster
picard> cluster lookup
picard> metadata show c1.f1
picard> save
```

The point is that what a command does is what the GUI does: it calls the same
`Workspace` operations (`add_files`, `move_files`, `cluster`, `save`, ...) and
builds the same views of the data (`picard.tagdiff.build_tag_diff` for the tags
the metadata box shows), so the two cannot drift apart.

## Commands

| command | what it does |
|---|---|
| `ls [sel]` | list top-level entities (or the selection) with their handles |
| `tree [sel]` | the working set as an indented tree, like the GUI panes |
| `file add <paths>` | load files, directories and globs, in filename order like the GUI; applies the GUI's ignore rules and placement policy (files with MusicBrainz IDs go to their album or track, `cluster_new_files` and `analyze_new_files` are honoured); skips files already loaded, and unsupported files it finds in a folder (one named explicitly is reported); a path that exists is taken as it is (`[1998]` in a folder name needs no escaping), `*`, `?` and `[...]` only act as a pattern when no such path exists |
| `cluster [sel]` | group files (default: unclustered) into clusters; a cluster stands for its files, an album or a track is refused (name its files, `a1.f*`) |
| `cluster lookup [sel]` | search MusicBrainz for clusters, auto-apply the best match, expose the alternatives as `m` handles (the console lists the best 10; `ls c1.m*` lists them all) |
| `match <cluster> <m>` | apply another candidate of that cluster |
| `lookup [sel]` | metadata lookup (autotag) of the selected objects |
| `url <sel\|mbid>...` | print the address of the MusicBrainz page of objects (release, recording, collection, or the tag lookup of a file or cluster that is not matched), on the server of the configuration; a MusicBrainz reference is accepted as well as an object |
| `open <sel\|mbid>...` | the same, and open the pages in a web browser (at most `open_max` at once, see `shell get`); if none can be started the addresses are shown |
| `refresh [sel]` | load the selected albums (and standalone recordings) again from MusicBrainz, like the Refresh action of the GUI (all the albums without a selector) |
| `scan [sel]` | identify files by AcoustID fingerprint |
| `album load <mbid\|url>` | load a release as an empty album; the reference may be a bare MBID, `release:<mbid>` or a MusicBrainz release URL |
| `album versions <album>` | list the other releases of the release group of an album, as the "Other versions" menu of the GUI does and in the same order (as many tracks as the album first, then the preferred countries and formats); each gets a `v` handle and the one the album is now is marked; requested from MusicBrainz the first time |
| `album switch <version>` / `album switch <album> <version\|mbid>` | switch an album to another release of its release group (`v2`, `a1.v2` — which say the album, so it can be left out — an MBID, `release:<mbid>` or a URL); the files are matched again to its tracks. The album keeps its handle unless that release is already loaded: the files go to that album, which is reported |
| `login [address]` | log in to MusicBrainz: `login` prints the address to open and, once Picard is authorized in the browser, finishes the login; `login <address>` finishes it with the address of the redirect when the browser is on another machine (see Account below) |
| `logout` | log out and revoke the authorization on MusicBrainz, for every Picard that uses it (destructive) |
| `collection ls` | the release collections of the user (needs a login), with a `k` handle each, their size and the albums of the working set that are in them |
| `collection add <k> <albums>` | add the releases of albums to a collection |
| `collection rm <k> <albums>` | remove the releases of albums from a collection |
| `disc read [device]` | read the TOC of the CD in a drive (by default the first of the `cd_lookup_device` option, as the GUI does) and load the matching release |
| `disc read-log <path>` | the same from a CD ripper log file |
| `disc read-tags <sel>` | the same from the disc information in the tags (`itunes_cddb_1`) of the files of the selection, which are matched to the release; needs no drive |
| `save [sel]` | write tag changes to disk |
| `metadata show <selector> [tag...]` | the tags of files, tracks, albums or clusters, as the metadata box shows them when they are selected; a tag is a name or a pattern (see below) |
| `metadata set <selector> <tag> <value>...` | set a tag, replacing its values (see below) |
| `metadata add <selector> <tag> <value>...` | add values to a tag, after the ones it has |
| `metadata rm-value <selector> <tag> <value>...` | remove values from a tag; a tag left with none is removed |
| `metadata rm <selector> <tag>...` | remove tags, by name or pattern |
| `move <sources> <destination>` | put files into a track (`a1.d2.t3`), a cluster, an album (matched to its tracks) or a bucket (`u`, `a1.u`), as dropping them in the GUI does (several files dropped on a track go to the following tracks of the album); the last word is the destination |
| `shell get [name]` | show the settings of the console: `open_max` (the most pages `open` opens at once, 5) and `minted_max` (the most handles written after `minted:`, 12); a number, `-1` for no limit |
| `shell history [count\|clear]` | list the lines typed in the console, numbered (the last `count`), or forget them all, in the console and in the history file |
| `shell remint [kind]...` | mint the handles of a kind (`f`, `c`, `a`, `t`, `m`, `v`, `k`) again from 1 when no object of that kind is left, else it is reported as `in_use` and nothing changes; without a kind, all are tried |
| `shell set <name> <value>` | set one for this session only, nothing is written to the configuration (`shell set open_max 10`) |
| `option ls [pattern]` | the options not at their default, or those matching a pattern, with where each value comes from |
| `option get <name>` | one option: value, default, type, title and source |
| `option set <name> <value>` | set an option for this session only |
| `option unset <name>` | forget the session's value of an option |
| `option save [names]` | write the options set in this session to the configuration (destructive) |
| `remove <sel>` | drop objects from the working set (never touches disk) |
| `trash <sel>` | move the files of the selection to the system trash (destructive) |
| `help [topic]` | list the commands and topics, or explain a command (`help move`), a group of commands (`help option`) or a topic (`help selectors`, `help paths`, `help tags`, `help quoting`) |

Names are currently a mix of flat (`save`, `remove`, `trash`, `scan`, `lookup`)
and `noun verb` (`cluster lookup`, `disc read`, `option set`, `metadata show`).
The `noun verb` form is the direction (see the Roadmap); the final names are not
decided.

A command is declared next to its function, with a decorator, in a module of
`picard/cli/engine/builtins/` (see "How it is built").

### Help

`help` lists the commands, each with a line, and the topics. `help <command>`
shows how to write the command (its usage, where `<x>` is required, `[x]`
optional and `x...` can be repeated) and explains it, with examples. `help
<group>` lists the commands of a group, and `help cluster` shows the command
and the ones that go with it (`cluster lookup`). The topics explain what is the
same for every command: `selectors`, `paths`, `tags` and `quoting`. Tab completes the names.

The text of a command is its docstring, written for the user, so there is one
copy of it. `help` is an engine command like the others and returns a result, so
that any frontend can show it; the quit and exit of the console are its own.

### The console

Besides the commands, the console has a few things of its own: `quit` and
`exit` (or Ctrl-D) leave, Ctrl-C cancels the line being typed or the command
that runs, and a command declared destructive (`trash`, `logout`, `option save`) is
confirmed first. The up and down keys recall the lines typed, also those of the
previous sessions: as in a shell, the history is kept in a file, readable by
the user only, and an empty line, a line typed twice in a row and a line that
starts with a space are not kept, and neither is `login <address>`, which holds the
authorization code of the login.
Several consoles can run at once: as bash does with `histappend`, each one adds
the lines of its session to the file when it ends (under a lock, except on
Windows), and the file is then cut to its size, so the lines of the others are
not lost; a console that is running does not see the lines of the others until
the next one starts. `shell history` lists the lines, and `shell history clear`
forgets them, for a line that should not have been kept. Two environment variables change it:

| variable | default |
|---|---|
| `PICARD_SHELL_HISTORY_FILE` | `shell_history` in the folder of the data of Picard (`~/.local/share/MusicBrainz/Picard` on Linux, `~/Library/Application Support/MusicBrainz/Picard` on macOS, `%APPDATA%\MusicBrainz\Picard` on Windows) |
| `PICARD_SHELL_HISTORY_SIZE` | the most lines kept, 1000; 0 keeps none, a negative number has no limit |

A line that starts with `!` is given to the shell of the system as it is, with
the terminal of the console: `!ls ~/Music/incoming`, `!mkdir /tmp/out`,
`!sha256sum *.flac | sort`. A command that fails is followed by its exit status.
Each one runs in a shell of its own, which could not change the directory of the
console, so `!cd <directory>` is done by the console itself: the commands that
follow start from there, and so do a relative path given to `file add` and the
completion of paths. `!cd` alone goes home and `!cd -` back. A `cd` among other
shell commands (`!cd /tmp && ls`) is the shell's and changes nothing for the
console. After the command, Tab completes paths.

### Tags

`metadata show <selector> [tag...]` shows what the metadata box of the GUI
shows when the entities of the selection are selected there (it builds the same
tag diff, `picard.tagdiff.build_tag_diff`, so the two cannot differ):

```text
picard> metadata show f1
f1  u.f1  shown  title=Song  filename=a.flac
    title      Song
    artist     Old Name -> New Name
    album      + Some Album
    genre      - Rock
    ~filepath  /music/a.flac
    ~length    3:05
```

A file has the tags it was loaded with and the ones it would be saved with, so
a tag is reported as unchanged, `->` changed, `+` added or `-` removed. A track,
an album or a cluster stands for its files (an album for the files of its
tracks, a track without a file for itself), as in the GUI, and the values that
differ between them are grouped: `title  (different across 3 items)`. Use a path
to look at one file (`metadata show c1.f2`). The tags are the visible ones, in
the order of the box (the top tags first), and the length and the name the file
would be saved with (`~length`, `~filepath`).

A tag is not an entity, so it has no handle and is not part of the selector: it
is a separate word after the selector. This is why the selector must be a single
word here (`f1,f2`, not `f1, f2`). A tag is its name, or a pattern with `*`,
`?` and `[...]` (`artist`, `musicbrainz_*`, `performer:*`: the colon is part of
the name of some tags). Without a tag, all those the box shows are listed; a
pattern that matches nothing is said.

`metadata set`, `add` and `rm` change the tags the way the metadata box does
(they use the same helpers, `picard.tagdiff.apply_tag_values` and
`merge_values`): the values that would be saved change, and nothing is written
to disk until `save`, so `metadata show` shows the result as changed, added or
removed. A track, an album or a cluster is changed together with its files, as
in the GUI. Each word after the tag is one value (quote a value with spaces, see `help quoting`;
`metadata set c1 genre Rock Pop` gives two values), `add` does not repeat a
value that is there, and `rm-value` takes values out of a tag (one that is left
with none is removed, as `rm` does). A value is never split on a semicolon: `show`
joins the values with `;` and a space to display them, so `Rock; Pop` is one value when it was set
as one, and the result of `show` carries the values as lists (`orig_values` and
`new_values`) for a frontend that needs them, unless the files of a selection
do not agree on them. A tag to set is a name, not a pattern, and cannot start
with `~` (those are variables of the scripts); `rm` takes patterns, and leaves
the tags that cannot be removed (the length and the file path). A file whose
format cannot hold a tag is left alone and reported as `unsupported`.

### Account

`login` and `logout` give the shell the account of MusicBrainz, which the
collections need (`collection ls`, `add` and `rm`, which also need the option
`enable_user_collections`, on by default).

MusicBrainz ends a login by sending the browser back to Picard on the loopback
address (`http://127.0.0.1:<port>/auth`, a port of the range of the browser
integration); it no longer shows a code to copy. `login` listens there, for
that redirect only, and prints the address to open. Once Picard is authorized
in the browser, `login` again finishes the login and reports the user name.
When the browser runs on another machine (the shell is used over ssh), the
redirect cannot reach the shell and the browser shows an error page: its
address holds the code, and `login <address>` finishes the login with it.
Forwarding the port over ssh works too.

- The tokens are stored in the configuration, as the GUI does. So logging in
  from the shell logs in every Picard that uses the same configuration, and a
  login made by the GUI is used as it is. This is the one deliberate write to the
  configuration besides `option save`; use a scratch configuration
  (`picard-cli -c ...`) to keep them apart.
- The login has to be finished in the same shell session that printed the
  address: the secrets that bind them (PKCE, and the state) are kept in memory.
- `logout` revokes the whole authorization on MusicBrainz, so every Picard that
  uses it is logged out. The console asks to confirm.
- With the GUI and the shell running on one configuration at the same time,
  MusicBrainz may issue a new refresh token on each use, so one process can
  invalidate the token of the other; a refresh that is rejected logs the user
  out in that configuration.
- A collection knows which releases are in it only through the albums loaded
  while logged in: an album loaded before the login is not shown in its
  collections by `collection ls`, though `collection rm` works on it.
  `collection add` skips the releases a collection is known to hold, and the
  sizes shown are those MusicBrainz gives after each change.
- Without a login, a request that needs one goes on without the user's data
  instead of waiting for a login nobody can give.

Possible improvements: finishing the login as soon as the browser comes back,
without a second `login`; the device authorization flow of OAuth, made for
machines without a browser, if MusicBrainz offers it; tokens kept for the session
only, so that a login does not touch the configuration; and retrying a refresh
with the token another process stored, before forgetting it.

Possible improvements to the collections:

- `collection show <k>`: the releases of a collection, one line each (the
  `release:<mbid>` reference, title, artist, date, country, format, tracks,
  and the handle of the album when it is loaded). MusicBrainz gives them 100 at
  a time (`mb_api.get_collection(id, handler, limit, offset)`, which has no
  caller yet), so it needs a function of `picard/collection.py` that fetches
  every page and calls back with the releases or an error, as
  `load_user_collections` does. Large collections take many requests, paced
  by the rate limit of the web service: a `--limit` may be needed.
- With the contents known, the collection knows which releases it holds, so
  `collection ls` and `collection add` no longer depend on the albums having
  been loaded while logged in.
- `collection load <k>`: load the releases of a collection as albums (today,
  `album load release:<mbid>` for each one).

### Options

Behaviour that depends on settings (where `save` puts files and how it names
them, what `file add` ignores, how lookups are scored, ...) is controlled with
the `option` commands. The rule is that **nothing is written to the
configuration unless you ask**: `option set` changes the option for the session
only, so an experiment cannot change the settings the GUI uses, and
`option save` is the one deliberate way to keep a value (it is confirmed by the
console, and written as the GUI would: into the profile that sets the option if
there is one, else into the configuration).

Each option is reported with where its value comes from, which answers "why is
`save` moving my files?": `session`, `profile <title>`, `config` (stored in the
configuration file) or `default`. `option ls` without a pattern lists only the
options that are not at their default.

It reuses the core's own pieces. A session value is held by an in-memory
"session" profile with the top priority, put in front of the user's profiles
with the overrides the options dialog uses, so `config.setting[...]` returns it
like any profile's value and no other code needs to know. The option registry
gives each option's type, default and title, and the option's own conversion and
bounds check the value (`true`/`false` for a yes/no option, a number within its
range, comma-separated items or a JSON array for a list).

This works for the options that take part in profiles (180 of the 192).
Interface and plugin state, the scripts and the AcoustID and fpcalc settings
can be shown but not changed for a session; set them in the configuration
file.

To try things on files without any risk, work on a copy of the files, and start
the shell on a scratch configuration so that no setting of yours applies:
`picard-cli -c /tmp/scratch.ini shell`, then set what is needed with `option
set`. A fresh configuration has none of your settings (for instance the
conversion of punctuation to ASCII), so results can differ from your usual ones.

## Handles, selectors and paths

Working-set entities get **session-local handles**: a type prefix + a
monotonically increasing ordinal, minted when the entity enters the session.
Handles are STABLE IDS, never positions: removing `a3` then `a4` does NOT
renumber; ids are never reused within a session, unless `shell remint` is asked to mint a kind from 1 again, once none of that kind is left (the ones that are there are never renumbered).

| prefix | entity            | source                       | lifecycle |
|--------|-------------------|------------------------------|-----------|
| `f`    | file              | `unclustered_files.files`    | session-lifetime; kept across reparenting |
| `c`    | cluster           | `clusters`                   | until removed |
| `a`    | album (incl. NAT) | `albums.values()`            | until removed |
| `t`    | track             | tracks within albums         | with its album |
| `m`    | match candidate   | lookup/scan output           | transient (until next lookup of target) |
| `k`    | collection        | `collection ls` output       | until the collections are loaded again and it is gone from them |
| `v`    | release version  | `album versions` output      | transient (until the versions of the album are listed again) |

Notes:
- `f*` is the UNCLUSTERED bucket only; files matched into albums/clusters are
  reached via their parent (`c1.f*`, `a1.f*`).
- A file keeps its handle for its whole session lifetime regardless of parent.
- Backed by weak references so removed entities' handles stop resolving rather
  than leaking. Implemented in `picard/cli/engine/handles.py` (`HandleRegistry`);
  the prefix classifier is injected so new kinds need no registry change.

A **selector** turns a reference into a set of entities. Implemented
(`picard/cli/engine/selectors.py`): single handles (`a1`), type wildcards
(`a*`), ranges (`f1-12`, `a1-3`, also in a path: `c1.f1-5`), the universal `*`
(all top-level objects: `f* ∪ c* ∪ a*`, as in the GUI panes, not tracks), paths
(below), and comma unions of those. A union may be
written with spaces and arrive as several command-line tokens (`ls a1, c2` or
`ls a1 c2`). A range selects the objects that exist among its numbers, in order (handles
are never reused, so a removed object leaves a hole), and is unresolved if there
are none; a reversed range (`a3-1`), one that starts at 0, one that mixes kinds
(`a1-c3`) and one of more than 10000 numbers are errors. Exclusion and sticky
bare ordinals are rejected with a clear error until they are implemented (see
the Roadmap).

Resolution gives `(entities, unresolved)`: tokens that matched no live entity
are reported, never silently dropped.

### Handles and paths

Every entity keeps a plain, stable handle (`f7`, `c1`, `a1`, `t12`, `m3`): its
identity, which follows it as it moves (a file keeps its handle from the
unclustered bucket to a cluster to a track) and which a result always reports.
A **path** is a second way to reach the same entities: segments separated by
`.`, each selecting children of the previous one. A path is a *position*, looked
up when the command runs, so it is convenient to type and to scope (`a1.d2`)
but does not follow an entity around. Scripts that keep a reference across
several commands should keep the handle.

| segment | under | selects |
|---|---|---|
| `u` | (start of a path) | the files that are in no cluster |
| `d<n>` | album | disc `n` of the release |
| `t<n>` | album, disc | track `n` (on that disc) |
| `f<n>` | album, disc, track, cluster | the `n`th file (`f*`: all of them) |
| `u` | album | the album's unmatched files |
| `m<n>` | cluster, file | the `n`th lookup candidate |
| `v<n>` | album | the `n`th version listed by `album versions` |

Examples: `a1.d2.t3`, `a1.d2` (the tracks of disc 2), `a1.t3.f1`, `a1.f*` (every
file of the album, matched or not), `a1.u`, `c1.f*`, `c1.m2`, `a1.v3`, `u.f*`.

- `*` and numbers work in any segment (`a*.t1`, `a1.d*.t1`).
- Discs and tracks of a release use the numbers MusicBrainz gives them (the
  `discnumber` and `tracknumber` tags), not list positions, so `a1.d2.t3` keeps
  its meaning when the album is reloaded. Other numbers (files, candidates) are
  positions in the order a listing shows.
- A release with one disc may leave the disc out (`a1.t3` is `a1.d1.t3`). With
  several discs the disc must be named: a selector that would otherwise guess
  (and, say, remove the wrong disc's track) is an error that lists the discs.
- Non-album tracks have no disc or track numbers: they are numbered by
  position and have no discs.
- Picard has no disc object, and the unclustered bucket is not a handle-able
  entity. A path ending at either stands for what it contains (a disc: its
  tracks; a bucket: its files), so results only ever hold entities that have a
  plain handle.
- A numbered step that finds nothing is reported as unresolved (`a1.t9`), a
  wildcard that matches nothing is an empty result, and a segment that makes no
  sense under its parent (`f1.t1`) is an error.
- At the top level `d` stays reserved for a disc ID / TOC (see the table
  above); under an album it means a disc of the release.

The console shows the path next to the handle (`t7  a1.d2.t3  listed ...`) and
tab-completes it: `ls a1.<TAB>` offers the segments that can follow `a1`, and so
on down the path. A session provides this through `path_of(handle)` (the path of
an entity) and `path_segments(base)` (what can follow a path).

## Result contract

Selector-taking commands return a per-handle outcome list plus resolution info,
distinguishing "resolved to empty" from "had unresolved tokens". Must be
serializable.

```text
EngineResult(
  ok         = True | False,
  items      = [ EngineItemResult(handle, path, status, data), ... ],
  resolved   = [handles...],     # what the selector matched
  unresolved = [tokens...],      # tokens matching no live entity (machine-actionable)
  mints      = [handles...],     # newly created handles
  message    = "...",            # optional human summary
  error      = "...",            # why the command failed (ok is False)
)
```

`unresolved` non-empty = the caller under-acted; `resolved == [] and
unresolved == []` = valid, nothing matched.

An item's `handle` is the entity's stable identity. Its `path` (`a1.d2.t3`,
`c1.f2`, `u.f1`, `c1.m2`; empty for albums and clusters, which are reached by
their handle) says where the entity sits *now*. The dispatcher fills it in, so
every command reports it; a consumer that keeps a reference across several
commands should keep the handle, and use the path to read or to type.

## How it is built

```text
Console (picard-cli shell) ── render ◄── EngineResult ◄── command ◄── dispatch ◄── line
                                                              │
                                                    EngineSession (interface)
                                                              │
                                            LocalEngineSession (headless)
                                            HandleRegistry · selectors · options
                                                              │
                                         Workspace / services / core (shared with the GUI)
```

Home: `picard/cli/engine/`; the console is `picard/cli/shell.py` with
`render.py` and `completion.py`.

1. **HandleRegistry** (`handles.py`) — mint/resolve handles, weak references,
   stable ids, injected classifier.
2. **Selector parser + resolver** (`selectors.py`) and the **path navigator**
   (`navigation.py`) — the subset described above.
3. **`EngineSession` interface, command declaration/registry, serializable
   `EngineResult`** (`commands.py`, `result.py`). A command declares its name,
   positional args, completion hints, its usage, a line for the list of
   commands, and whether it is `destructive` (an interactive frontend asks before
   running it). The docstring of the function is the help of the command.
   `topics.py` has the texts of the topics, `builtins/help.py` the `help`
   command, made for the registry it describes.
4. **`LocalEngineSession`** (`session.py`) — owns the handle registry, the
   resolver, the options of the session and the lookup candidates (held weakly
   per looked-up target), and drains async work with `run_until_idle`. A command
   that stops waiting reports it in its result (a message, and a `pending` /
   `timeout` status where the outcome is unknown) instead of looking successful.
5. **Dispatch** (`dispatch.py`) — command line to command invocation, always
   returning an `EngineResult`.
6. **Built-in commands** (`builtins/`) — a command is a function
   `(session, args) -> EngineResult`, declared where it is implemented:

   ```python
   @command('metadata show', help="...", args=('selector', 'tags'), arg_kinds=('selector', 'tag'))
   def _cmd_metadata_show(session, args): ...
   ```

   The modules group them by what they act on: `listing` (`ls`, `tree`),
   `files` (`file add`, `save`, `move`, `remove`, `trash`), `identify`
   (`cluster`, `cluster lookup`, `match`, `lookup`, `scan`, `album load`),
   `versions` (`album versions`, `album switch`), `account` (`login`,
   `logout`), `usercollections` (`collection ls`, `add`, `rm`), `metadata`,
   `option`, `disc`.
   `helpers` has what they share, and importing the package declares them all
   in one registry.

### Rules

- Commands return **structured, serializable `EngineResult`** objects and never
  print or touch transport. Only frontends render. A result is plain data, with
  no live object references, so that it can be serialized (`to_dict()`) or sent
  to another process.
- **Handles are the serializable proxy for entities.** A result references
  entities by handle string (`a1`), never by object.
- **Handles live engine-side.** The session that owns the entities owns the
  `HandleRegistry`.
- **`EngineSession` is an interface.** Commands are written against it and do
  not know which implementation they run on (see the Roadmap).

### Async model

A command = mutate the working set → drain async work → return a result.
`run_until_idle()` pumps the event loop until thread pools, pending web requests,
fingerprinting and the batches still to run settle (or a timeout, which the
result reports). The caller sees a synchronous-looking command.

## Roadmap (not implemented)

What follows is the design the engine is meant to grow into. It is a target
contract, not a commitment to implement all of it.

### Two backends

One command vocabulary over **two interchangeable execution backends**:

- **Local / headless** (done) — commands run in-process against a
  `HeadlessTagger` + `Workspace`.
- **Remote / GUI** — the *same* commands sent to an already-running GUI Picard
  and executed against its live `Tagger` + `Workspace`; this backend could also
  trigger GUI-only actions (views, window, help, menu actions).

The commands are written against the `EngineSession` interface so that a
`RemoteEngineSession` can satisfy it by proxying to the GUI over the existing
pipe/socket (which would need a response channel: it is one-way today). Nothing
else about the commands would change. A command that only makes sense with a
GUI (`window raise`, `play`, any `MainAction` chrome) would declare so, and the
local session would not offer it; that declaration is added with the first such
command.

This would **replace the current remote-command system** (`picard/remotecommands/`,
flat pipe verbs reaching into `self.tagger.*`): its handlers already retire as
the orchestration moved onto `Workspace`, and one console could do everything the
`-e` remote commands did, plus everything headless does.

A second frontend is an **AI agent over MCP**: structured tool calls instead of
a REPL, one tool per command (`album_show`, `metadata_add`), the same
`EngineResult.to_dict()` as the payload.

### Naming: `<noun> <verb>`

Commands are meant to be `noun verb [args]`: `option set`, `metadata add`,
`album show`, `cluster remove`, `disc lookup`. Rationale: namespaces cleanly (no
`set`/`get` collision between options and tags), self-groups for help and
discovery, and maps directly to MCP tool names. It supersedes the flat vocabulary
(`save a1` → `album save a1` / `file save`).

### Full selector grammar

```ebnf
selector  = term , { "," , term } ;
term      = [ "!" ] , atom ;                 (* ! = exclude *)
atom      = scoped | bare ;
scoped    = prefix , selement ;              (* a1, a1-3, a*  *)
bare      = selement ;                       (* 2, 1-3 — inherits sticky prefix *)
selement  = range | ordinal | "*" ;
range     = ordinal , "-" , ordinal ;        (* a1-3 *)
ordinal   = digit , { digit } ;
prefix    = "f" | "c" | "a" | "t" | "m" | "v" | "d" | "k" ;
```

On top of what is implemented (ranges are, `a1-3` and `a1.t2-4`): exclusion (`a*,!3` is all albums but `a3`, a set difference over
the whole expression), sticky prefixes for bare ordinals (`a1,2,c3,4` is
`a1,a2,c3,c4`), and `prefix where <field>=<value>` metadata selectors. Further
handle kinds: `d` (a disc ID / TOC); at the top level `d` stays reserved for
the disc ID, and under an album it means a disc of the release. "Every file everywhere" would be
a separate token (`files:all`).

### Capability taxonomy (TARGET — build incrementally)

Derived from Picard's full GUI action surface (`picard/const/actions.py`
`MainAction`), so the vocabulary is complete-by-construction.

The names below are the TARGET vocabulary. Commands already implemented keep
their current names (see "Commands"): `file save` is `save`,
`file remove` is `remove`, `file trash` is `trash`, `file scan` is `scan`,
`album lookup` is `lookup`, `disc lookup` is `disc read` and `disc from-log` is
`disc read-log`.

#### Working-set nouns

| noun · verb | backing | mints | notes |
|---|---|---|---|
| `file add <paths>` | load files | `f` | ADD_FILES / ADD_DIRECTORY |
| `file save <sel>` | `File.save` | — | SAVE |
| `file remove <sel>` / `file trash <sel>` | Workspace.remove / trash_files | — | REMOVE / TRASH |
| `file move <sel> <target>` | Workspace move | — | |
| `file scan <sel>` | AcoustID fingerprint lookup | `m` | — |
| `file info <sel>` | technical + tag info | — | VIEW_INFO |
| `cluster <sel>` | Workspace clustering | `c` | CLUSTER |
| `cluster remove <sel>` | Workspace.remove_cluster | — | |
| `cluster lookup <sel>` | tag-based lookup | `m` | |
| `cluster submit <sel>` | submit as release | — | SUBMIT_CLUSTER |
| `album lookup <sel>` | metadata lookup | `m` | |
| `album save/remove/refresh <sel>` | File.save / remove_album / reload | — | REFRESH |
| `album versions <sel>` | release-group versions | `v` | ALBUM_OTHER_VERSIONS (done) |
| `album switch <a> <v>` | switch_release_version | — | (done) |
| `track show <sel>` / `track move` | — | — | |
| `metadata show <sel> [tag...]` | orig/new tags | — | the metadata-box equivalent (done) |
| `metadata set/add/rm-value/rm <sel> <tag> [value...]` | apply_tag_values / merge_values (done) | — | multi-value via list, not joiner |
| `cover show/set/rm/export <sel>` | cover art | — | the cover-art-box equivalent |
| `candidate ls/show <sel>` | — | — | produced by lookup/scan/search |
| `match <target> <m>` | apply candidate (move_files_to_album/…) | `a` | |
| `ls [sel]` | session view | — | |

#### Identify / submit

| noun · verb | backing | mints | notes |
|---|---|---|---|
| `disc lookup` | read drive (discid) → MB | `m`/`d` | CD_LOOKUP — forces disc headless story |
| `disc from-log <file>` | parse rip log | `m`/`d` | DISCID_FROM_LOGFILE |
| `disc from-tags <sel>` | derive TOC from tags | `m`/`d` | DISCID_FROM_TAGS |
| `search album/track/artist <query>` | MB search | `m` | ALBUM/TRACK_SEARCH |
| `acoustid submit <sel>` | submit fingerprints | — | SUBMIT_ACOUSTID |
| `isrc submit <sel>` / `isrc lookup` | ISRC | — | SUBMIT_ISRC / LOOKUP_ISRC |
| `fingerprint <sel>` / `analyze <sel>` | compute fingerprints | — | GENERATE_FINGERPRINTS / ANALYZE |

#### Session / config / collections

| noun · verb | backing | notes |
|---|---|---|
| `session save/load <path>` / `session new` | picard/session + clear_session | SAVE/LOAD/NEW_SESSION |
| `option set/get/unset/ls <key> [val]` | `config.setting[...]` | — |
| `profile ls/use/show <name>` | option profiles | existing CLI machinery |
| `plugin ls/install/remove/update` | plugin manager | existing `picard-cli plugins` |
| `collection ls/add/rm` | MB user collections (done) | OPEN_COLLECTION_IN_BROWSER etc. |
| `collection show <k>` | the releases of a collection, from MusicBrainz (not done, see Account) | needs a core wrapper of `get_collection` with paging |

#### GUI-only (a remote session only)

`view metadata/coverart/filebrowser show|hide`, `window raise/close`,
`help show`, `play <sel>` / `play external`, `browser lookup <sel>`,
`similar-items search`, plus any remaining `MainAction` chrome
(about/donate/report-bug/check-update). These drive the running GUI; a
local (headless) session has no GUI to drive, so these would not exist there.

### Unifying insights

- `lookup` / `scan` / `search` / `disc lookup` all PRODUCE candidates (`m*`),
  auto-applying the top match but leaving the rest addressable; `match` ACCEPTS
  one. `album versions` / `album switch` are the separate same-release-group
  mechanism.
- `metadata show`, `set`, `add` and `rm` (done) are the metadata-box
  equivalent; `cover …` the cover-art-box equivalent. Backed by core `Metadata`
  (`getall`, `set`, `add`, `delete`) and the shared tag diff, so console and GUI
  show the SAME diff. For an agent, `metadata show` is "preview exactly what a
  save will change" before `album save`.

### Options model

- Session-global: `option set/get/unset`. Affects the whole session.
- Per-command flags only where an op has a genuine one-shot variant
  (`album save a1 --no-rename`), declared as command params so MCP gets tool
  params and the console gets `--flags`. The long tail stays in `option set`.
- `profile use <name>` reuses existing profile machinery.

### Worked examples

Console (local or remote — identical):
```text
picard> file add ~/Music/incoming/*.flac
added 14 files → f1–f14
picard> cluster f*
→ c1 (Radiohead – OK Computer, 12), c2 (unknown, 2)
picard> album lookup c1        # cluster → candidates
c1 → m1 ★auto→a1 (0.94), m2 (0.88), m3 (0.41)
picard> match c1 m2
c1 → a2, 12/12
picard> metadata show a2       # the metadata-box equivalent
  title/… orig vs new vs Δ …
picard> metadata set t3 title "Paranoid Android"
picard> album save a2
```

MCP (agent):
```jsonc
→ cluster({"selector":"f*"})
← {"mints":["c1","c2"], "items":[{"handle":"c1","title":"OK Computer","file_count":12}, …]}
→ album_lookup({"selector":"c1"})
← {"items":[{"handle":"c1","candidates":[
     {"handle":"m1","mbid":"dd66…","score":0.94,"applied":true,"album":"a1"},
     {"handle":"m2","score":0.88}]}]}
→ metadata_show({"selector":"a1"})
← {"items":[{"handle":"t1","tags":{"title":{"orig":["Pyramid Song"],"new":["Airbag"],"status":"changed"}, …}}]}
→ album_save({"selector":"a1"})
← {"items":[{"handle":"a1","saved":12}], "unresolved":[]}
```

### Not done yet

The rest of the catalog, `RemoteEngineSession` and the pipe response channel,
gui-only commands, `collection show`, sessions, profiles, the MCP
frontend, restoring the original value of a tag, and the cover art.
