*2012.08.25 13:10:11 sass compass css
converting style.css to use SASS and Compass libraries
this should improve re-usability *and* keep style.css more up to date

sudo gem update --system
sudo gem install sass
sass --watch sass:css

*2012.09.02 07:46:17 
it is possible to compile sass/scss files with python or javascript compilers as well:
https://github.com/bmavity/scss-js
https://github.com/Kronuz/pyScss

*2012.09.02 17:34:51 
I like the idea of developing styles in SASS and then converting to LESS... that is a very easy conversion to automate:
the best way is to convert to SCSS first, then you should be able to do a find/replace of @mixin and @include. If your editor has regexp find/replace, something like s/@mixin /\./g, so @mixin foo gets replaced by .foo - and you can replace the variables with s/\$(\w+):/@\1:/g. That should cover most of it.

It is not as easy to go the other direction, since LESS mixins start with a . (both the call and the definition)  I also think this makes the markup more difficult to read. 
http://stackoverflow.com/questions/3872728/converting-sass-to-less

also [2012.09.03 08:39:31] 
few other gotchas going from one to the other
LESS:                SASS:
spin()               adjust-hue()
e(~"")               #{}




*2012.08.25 13:32:21 compass
will see mention of 
blueprint is a grid based layout system

with Compass, do *not* use blueprint 
it is going away... (http://compass-style.org/blog/2012/05/20/removing-blueprint/)

for help generating responsive grids in CSS, Susy works with compass:
http://susy.oddbird.net/guides/getting-started/

also [2012.08.25 14:30:09] install
sudo gem update --system
sudo gem install compass
#this will also install SASS + other dependencies

also [2012.08.25 14:31:21] new_project
compass create template

results in:

Congratulations! Your compass project has been created.

You may now add and edit sass stylesheets in the sass subdirectory of your project.

Sass files beginning with an underscore are called partials and won't be
compiled to CSS, but they can be imported into other sass stylesheets.

You can configure your project by editing the config.rb configuration file.

You must compile your sass stylesheets into CSS when they change.
This can be done in one of the following ways:
  1. To compile on demand:
     compass compile [path/to/project]
  2. To monitor your project for changes and automatically recompile:
     compass watch [path/to/project]

More Resources:
  * Website: http://compass-style.org/
  * Sass: http://sass-lang.com
  * Community: http://groups.google.com/group/compass-users/


To import your new stylesheets add the following lines of HTML (or equivalent) to your webpage:
<head>
  <link href="/stylesheets/screen.css" media="screen, projection" rel="stylesheet" type="text/css" />
  <link href="/stylesheets/print.css" media="print" rel="stylesheet" type="text/css" />
  <!--[if IE]>
      <link href="/stylesheets/ie.css" media="screen, projection" rel="stylesheet" type="text/css" />
  <![endif]-->
</head>

also [2012.08.25 14:48:50] 
updating config.rb and default location to work better with tempates/web

/c/mindstream/templates/web 
compass compile .



*2012.09.02 08:18:15 modular_scale
http://thesassway.com/projects/modular-scale

https://github.com/scottkellum/modular-scale

gem install modular-scale

Add:

require 'modular-scale'

to your Compass config file.
Import the file into your stylesheets: 

@import 'modular-scale';




also [2012.08.25 15:16:45] susy grids 
sudo gem install susy

add:
require "susy"

to config.rb

@import "susy";

also [2012.08.26 18:28:32] compass
this does not seem to work at this time
    @include single-transistion(all, .2s, linear)



*2012.09.02 08:14:39 bourbon
bourbon is a newer alternative to compass:

https://github.com/thoughtbot/bourbon

http://stackoverflow.com/questions/7666572/compass-vs-bourbon-frameworks

currently modular-scale is using compass, so might not have a chance to investigate further at this time. 

http://thoughtbot.com/bourbon/#golden-ratio










*2012.08.25 13:24:45 less
the other alternative for CSS abstraction is LESS
the only positive LESS has over SASS is that it is written in Javascript instead of Ruby.  People really rave about Compass though, so I'm going to start with that one. 

also [2012.08.30 07:53:55] 

  <!-- production CSS *should* be precompiled!!!
  <link href="css/base.css" rel="stylesheet" type="text/css" />
  -->

  <!-- use less (lesscss.org) to compile stylesheet dynamically 
       don't forget to add '#!watch' to the browser URL while developing 
       (this approach does not work with local files... must serve via HTTP) 
  <link rel="stylesheet/less" type="text/css" href="css/style.less">
  <script src="js/libs/less-1.3.0.min.js" type="text/javascript"></script>
  -->

also [2012.09.02 06:53:46] 
there is a command line version of less (lessc) that gets downloaded to the local path when installed with node package manager npm.  
(there is http://incident57.com/less/, but it's not open)

Twitter's Bootstrap package uses less for their stylesheets... that's a pretty big endorsement.

http://www.wordsbyf.at/2012/03/08/why-less/


*2012.09.02 07:47:36 
LESS and SCSS are very similar...
would be feasible to convert between one or the other:

https://www.google.com/search?q=convert+between+sass+and+less&sugexp=chrome,mod=1&sourceid=chrome&ie=UTF-8
http://stackoverflow.com/questions/3872728/converting-sass-to-less
http://stackoverflow.com/questions/3133204/less-or-sass-scss-when-doing-non-ruby-projects?rq=1



*2012.08.30 07:56:38 stylus
finally, there is also stylus
http://learnboost.github.com/stylus/docs/executable.html

