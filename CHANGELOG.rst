CHANGELOG
=========

Revision 71feeba (30.06.2014, 08:31 UTC)
----------------------------------------

* LUN-1684

  * blog pages should only respond to urls that start with /blogs
  * allow proxy prefixes in the blogs urls

No other commits.

Revision 5f21b50 (20.06.2014, 11:53 UTC)
----------------------------------------

* LUN-1671

  * , LUN-1676: fixed navigation between entries; re-fixed blog related url patterns
  * fixed urls so they only match it it starts with blogs

* LUN-1676

  * LUN-1671, LUN-1676: fixed navigation between entries; re-fixed blog related url patterns

* LUN-1678

  * Fix Save button not working after alert is displayed

* LUN-1680

  * dot from filename extension should be stripped.

* Misc commits

  * Remove len(uploaded_poster_image)==CONTENT_LENGTH.

Revision a0cd378 (18.06.2014, 15:39 UTC)
----------------------------------------

* LUN-1655

  * Move help text on the left to avoid tooltip beeing cut off when window is too small

* LUN-1665

  * Add support for timezones that are not multiple of hours
  * Fix calendar not beeing displyed in IE 10 - this occured when the user was set in Pacific Time and the offset wasn't included in   the date string (ex: Wed Jun 18 05:21:38 PDT 2014) so the regex failed - to fix this get timezone programaticaly using the Date object methods

* LUN-1667

  * should not allow titles that generate empty slug

* Misc commits

  * Minor css fix for font size
  * Fix entry text on small break points
  * Increase image max upload size to 2.5 MB

Revision 99d6541 (16.06.2014, 14:40 UTC)
----------------------------------------

* LUN-1651

  * Fix help text alignment in FF and IE
  * Fix help text icon in FF, fix entry description

* LUN-1652

  * blog menu node text should be max 15 chars

* LUN-1653

  * Fix navigation popup not closing

* LUN-1656

  * change 480 breakpoint to be inclusive

* Misc commits

  * Fix blog header height when no image is present
  * help text changes

Revision 547f41e (13.06.2014, 16:22 UTC)
----------------------------------------

* LUN-1621

  * Add link to entry image in blog landing page and river plugin

* LUN-1642

  * fixed tests since blog creation now requires a home page on the working site.
  * a default layout will get generated for a new blog.

* LUN-1643

  * current user should be added in the blog allowed users on creation.
  * added categories to list display; * in order to not affect performance too much, restricted items per page to 50

* LUN-1645

  * Fix text deisplayed under poster image

* LUN-1648

  * changed help text + added help tooltips

* LUN-1650

  * Make header image only 100

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
