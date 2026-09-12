================================================================================

   D A B B L E      C O N T E N T

   One folder per image card. Everything on the site is generated from this
   folder, and this folder is the only place content should be edited.

================================================================================



   ADDING AN ENTRY
   ---------------------------------------------------------------------------

   1.  Copy the _TEMPLATE folder, and rename the copy.

       Name it a short slug  -  for example  tidal-atlas  -  the folder name
       is just an id, so pick something readable that isn't already taken.
       Folders starting with _ are ignored.

       The order on the page is set by the  order:  field in entry.md (see
       below), NOT by the folder name - so you never have to claim a number,
       and two people can add cards at the same time without clashing.


   2.  Put exactly ONE image in       main/

       This is the image that floats in the swirl on the front page, and
       heads the card when someone opens it.

       The build stops with an error if this folder is empty, or if it has
       more than one image in it. That is deliberate - it should never have
       to guess which one you meant.


   3.  Put any number of images in    supporting/      (or none at all)

       These sit partway down the card, between the two blocks of copy.
       They never appear in the swirl. Each one runs the full width of the
       card at its own proportions - nothing is cropped, so a wide screenshot
       stays wide and a tall photograph stays tall.

       They are shown in filename order, so name them 01- 02- 03- to
       control the sequence.

       To caption one, put a text file of the same name beside it:

           supporting/01-workshop.jpg
           supporting/01-workshop.txt      <- the caption for it

       The caption prints in small caps under the image. One line is
       plenty. Leave the file out, or leave it empty, and the image simply
       runs without a caption - the build lists which ones are still
       waiting, so nothing gets quietly forgotten.


   3b. Optional - a carousel for image-heavy projects.

       If a project has a lot of images and you do not want them all running
       full width down the card, make a   carousel/   folder inside
       supporting/  and put the extra images there:

           supporting/carousel/01.jpg
           supporting/carousel/01.txt      <- an optional caption

       On the Stories / Dabblers case study these appear as a compact
       carousel - one image at a time, with arrows - below the full-width
       supporting images, so a big set does not push the rest of the page
       down. The carousel shows up only when that folder has images in it;
       an empty or missing  carousel/  simply means no carousel. Captions
       here are optional and are not nagged about. (This is a gallery-page
       feature - the hero swirl and the full-width supporting images are
       unchanged.)


   4.  Fill in                        entry.md

       See the next section.


   5.  Rebuild.

           cd ~/Desktop/dabble\ website/hero-peel
           python3 build.py

       About two seconds. The new entry joins the swirl and its galleries
       automatically. Nothing else needs editing anywhere.

       The build writes every page of the site:

           dabble-hero-peel.html    the front page
           stories.html             Stories gallery
           dabblers.html            Dabblers gallery
           our-team.html            Our Team
           about.html               About
           contact.html             Contact

       Each nav link on the lifted page goes to its own file.



   ENTRY.MD
   ---------------------------------------------------------------------------

   The top block, between the two --- lines:

       order       Optional. A number setting where the card appears -
                   lower comes first. Leave it out (or leave it high) and
                   the card lands at the end, for a maintainer to place.

       title       The heading on the card.

       subtitle    The small line above the title.

       story       yes  puts this card in the STORIES gallery.

       dabbler     yes  puts this card in the DABBLERS gallery.

       credits     The collective members who worked on it. One name per
                   line, each starting with two spaces and a dash:

                       credits:
                         - Kelly Chou
                         - Someone Else

                   These become the mini-mentions under each person on the
                   Our Team page.

       caption     The small line at the very bottom of the card, under a
                   rule. Credit, date, source - whatever suits.


   story and dabbler are independent of each other:

       both yes    the card appears in both galleries
       both no     the card still floats in the swirl, but appears in
                   neither gallery. The build prints a note when this
                   happens, in case it was not what you meant.


   Underneath that block, the body copy sits between two markers:

       :: ABOVE ::      copy that appears above the supporting images
       :: BELOW ::      copy that appears below them

   Both are optional. Write as many paragraphs as you like under each -
   just leave a blank line between them. An entry with no supporting
   images simply runs its copy together.



   THE TEAM
   ---------------------------------------------------------------------------

   The Our Team page is built from two things in the  team/  folder, one level
   up from here:

       team/team.csv          one row per person
       team/<photo>           the headshots

   team.csv has four columns:

       name      shown under the headshot
       role      small line under the name. Optional - leave blank and
                 nothing is shown.
       bio       the short description. Optional in the same way.
       photo     the filename in team/  e.g.  kel.webp

   Row order is the order on the page, so reordering rows in a spreadsheet
   reorders the page. Open it in Numbers, Excel or Sheets - just save it back
   as CSV, not .xlsx.

   The paragraph under the headshots comes from  team/intro.txt  - plain text,
   a blank line between paragraphs. Leave it empty and no paragraph appears
   at all; there is no placeholder text anywhere on the site.

   The page is just the ten headshots in two rows of five and that paragraph.
   Hovering a headshot shows the person's name; clicking one opens their
   profile over the page - portrait, name, role, bio, and the titles of any
   entries they are credited on. Esc or Close dismisses it.

   Someone with no role and no bio still gets a headshot and a profile; the
   empty parts are simply left out rather than shown blank.

   The dabble mark sits bottom left and goes back to the front page. The
   corner lifts here just as it does on the front page, with the same five
   links underneath - so you can get anywhere without going back first.

   Following a link finishes the lift first: the paper covers the screen,
   the links fade, and the next page opens on that same blank cream with the
   same black mark and eases its content in. The two pages are separate
   files, but the change is not meant to be visible.

   To add someone: drop their headshot in team/ and add a row. To remove
   someone, delete their row. Then rebuild as usual.

   The build tells you who is missing a bio or a photo, and warns about a
   headshot in team/ that no row uses.

   Anyone named in an entry's  credits:  gets that entry listed under them
   as a PROJECTS mention on their profile. The name has to match team.csv -
   the build says so if it doesn't, rather than quietly dropping it.

   The mention shows the entry's  subtitle  (e.g. "Paperboy . 2026"), not its
   title - because in this schema  title  holds the question and  subtitle
   holds the short name. Worth knowing when you write new entries: keep the
   subtitle short enough to read as a project name.


   IMAGES
   ---------------------------------------------------------------------------

   Drop in the full-size original. The build resizes and compresses for you,
   every time it runs. You never export a web version by hand.

   JPEG, PNG, WebP, TIFF and HEIC all work.

   Replacing a stock image is just swapping the file in main/ and
   rebuilding. Nothing anywhere refers to images by filename, so the new
   file can be called anything.

   Where they end up - all of them become files under  hero-peel/assets/ :

       main/          assets/<entry>/main.jpg      at 1280px
       supporting/    assets/<entry>/<name>.jpg    at 1600px
                      (a .txt of the same name is the caption, not an image,
                       and stays where it is)
       supporting/carousel/
                      assets/<entry>/carousel/<name>.jpg   at 1600px
       team/          assets/team/<name>.jpg       at 640px

   The pages themselves are tiny (about 60 KB) so they appear straight away,
   and the photographs load in behind them. If you ever move the site
   somewhere, the HTML files and the assets folder have to travel together.



   REBUILDING  -  worth knowing
   ---------------------------------------------------------------------------

   The page is a snapshot, not a live view. It is the same relationship as
   an InDesign document and a PDF you exported from it: changing the
   document does not change the PDF until you export again.

   So if you swap an image, save entry.md, then open the page and see the
   old version - nothing is broken. You just have not rebuilt yet.

       edit  ->  save  ->  python3 build.py  ->  refresh the browser

   To check the build can run on this machine at all:

       python3 build.py --backend

   That prints which image tool it will use and exits without building.



================================================================================

   STATUS  /  STILL TO DO

================================================================================


   The whole site now builds: front page, Stories, Dabblers, Our Team, About
   and Contact. What is left is content rather than code:

   -  Real copy and real images for some entries. Check each entry.md reads
      the way you want and that main/ holds the intended photo, not a
      placeholder.

   -  Bios and roles in  team/team.csv , and the paragraph in
      team/intro.txt . The build lists who is still missing a bio or photo.

   -  Captions for supporting images. The build lists any that are still
      empty, so nothing is quietly forgotten.

   For how to contribute a new card as a pull request, see CONTRIBUTING.md
   at the top of the repository.
