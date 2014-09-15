Troubleshooting
###############



Getting help
============

If you have problems using Picard, please first check the following
resources:


+ For general usage information see the documentation and the
  :ref:`illustrated quick start guide <guide>`
+ Read the :ref:`FAQ <picard-faq>` for common questions and problems
+ Consult the `forums`_.
+ Check the `download page`_ for a newer version of Picard which might
  solve your problem
+ If the problem is to do with a plugin, check the `Picard Plugins`_
  for updated plugin versions.




Reporting a bug
===============

If you think you have found a bug please check whether you are using
the `latest version`_ of Picard and whether the bug has already been
reported in our `bug tracker`_. If you're not sure or don't want to
look through the existing tickets, ask on the `forums`_ first.

If you're still convinced you have found a new bug, open a `new
ticket`_ providing the following information:


+ Which version of Picard do you use? ( **Affects Version** in the
  form)
+ Which operating system do you use? ( **Environment** in the form)
+ What did you do when the bug occurred?
+ What actually happened and what did you expect to happen?
+ If you're using plugins, which plugins do you have enabled?




Getting logs
============

For many bugs, it helps developers to have a log from Picard. You can
see the log by going to **Help** >> **View Log**. You can also get a
full debug log (even better) by starting Picard with **-d** as a
command-line argument. If you're using Windows, you can change your
shortcut's Target (right click shortcut >> **Properties**) to

::

    "C:\Program Files\MusicBrainz Picard\picard.exe" -d

Pasting this log into your forum post or bug ticket can help
developers and other users to resolve your issue more quickly.





.. _bug tracker: http://tickets.musicbrainz.org/browse/PICARD
.. _documentation: http://picard.musicbrainz.org/docs/
.. _download page: http://picard.musicbrainz.org/downloads/
.. _forums: http://forums.musicbrainz.org/viewforum.php?id=2
.. _latest version: http://picard.musicbrainz.org/
.. _new ticket: http://tickets.musicbrainz.org/secure/CreateIssue.jspa?pid=10042&issuetype=1
.. _Picard Plugins: http://picard.musicbrainz.org/plugins/

