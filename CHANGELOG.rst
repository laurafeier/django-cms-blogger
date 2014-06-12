CHANGELOG
=========

Revision e0ab12a (12.06.2014, 12:53 UTC)
----------------------------------------

* LUN-1631

  * changed fieldset text

* LUN-1635

  * should not allow empty author names.

* LUN-1636

  * Remove image Credit/Caption on blog landing page and blog promotion plugin

* LUN-1638

  * poster image should not be displayed in the entry page unless it's enabled
  * added poster image display switch.
  * Changed some poster image help text/label

* LUN-1639

  * Update entry unpublish help text

* Misc commits

  * added tests
  * Fix number of blogs and entries in changelist.
  * Remove dafult entry H1 margin for pages that do not use bootstrap css
  * remove useless space
  * Fix title and category related messages.

Revision 8504886 (10.06.2014, 15:44 UTC)
----------------------------------------

* LUN-1626

  * Fix blog entry admin buttons after 'Reset' is pressed in FF

* LUN-1630

  * code style changes
  * if cdn domain is provided, use it as a custom domain and serve files from it.

* Misc commits

  * Drop entry pagination 'newer'/'older' text on small breakpoints
  * Prevent some style to be overridden by station styles
  * Fix menu going under blog banner

Revision 4092525 (06.06.2014, 09:05 UTC)
----------------------------------------

* LUN-1603

  * all poster images should have a fixed width/height. Smaller images will get a transparent background.

* LUN-1618

  * ignore empty values for date time widget

* Misc commits

  * improve query for getting categories names and ids
  * don't allow regular users to move entries; +tests
  * test move nothing; pep8 forms.py
  * don't test entries.exists(), entries could be []
  * river should diplay its title in the placeholder admin
  * refactoring tests; +pep8
  * changed docstring
  * don't use post_data; don't use redundant list()
  * rename blogentries to entries
  * don't use post_data; add tests for redundant moves
  * comment change.
  * test with saved entries, and one draft entry
  * increment duplicate slug when moving entry; +tests
  * minor stuff
  * move blog entries to a blog

Revision cfd3bf4 (05.06.2014, 11:59 UTC)
----------------------------------------

* LUN-1611

  * fix blog entries pagination display issues

* LUN-1612

  * , LUN-1613, LUN-1614: fix display issues on blog entry

* LUN-1613

  * LUN-1612, LUN-1613, LUN-1614: fix display issues on blog entry

* LUN-1614

  * LUN-1612, LUN-1613, LUN-1614: fix display issues on blog entry

* LUN-1620

  * Show title instead of description, remove date in entry footer

No other commits.

Revision 88c7b30 (03.06.2014, 10:37 UTC)
----------------------------------------

* LUN-1592

  * changed widget for categories in blgo river plugin.

* LUN-1594

  * fixed getting last position in the root nodes.

* LUN-1595

  * added momentjs to blog entry admin in order for the date string to be parsed correctly.

* LUN-1598

  * Fix prev/next not displayed side by side in FF

* LUN-1599

  * URL encode params for social plugins

* LUN-1601

  * Fix entry author field not expanding for long author list

* LUN-1604

  * Use escape() instead of escapejs() to HTML escape menu preview HMTL

No other commits.

Revision fe37dbb (02.06.2014, 12:24 UTC)
----------------------------------------

* LUN-1588

  * Fix blog river entry template

* LUN-1589

  * comment out search box
  * Remove search box from blog

* LUN-1590

  * Added site domain in the view on site url.

* LUN-1593

  * Improve blog river loading experince, fix 'Read more' button
  * move blog targeting js to css block

* LUN-1595

  * toLocaleString does not seem to work on all browsers. Fixed by using toString.

* Misc commits

  * Make sure blog css is not overidden by station custom css

Revision d23fb64 (30.05.2014, 08:52 UTC)
----------------------------------------

Changelog history starts here.
