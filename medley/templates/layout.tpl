<!doctype html>
<!--[if lt IE 7]> <html class="no-js lt-ie9 lt-ie8 lt-ie7" lang="en"> <![endif]-->
<!--[if IE 7]>    <html class="no-js lt-ie9 lt-ie8" lang="en"> <![endif]-->
<!--[if IE 8]>    <html class="no-js lt-ie9" lang="en"> <![endif]-->

<!-- Consider adding a manifest.appcache: h5bp.com/d/Offline -->
<!--[if gt IE 8]><!--> <html class="no-js" lang="en"> <!--<![endif]-->
<head>
  <title>{{title or 'Collections'}}</title>
  
  %# if you want to customize these on a page by page basis, 
  %# remove them here and pass them in from the calling page 
  % description="Application to help sort and track media in collections"
  % keywords="collections media database"
  % author="Charles Brandt"

  <meta name="description" content="{{description}}" />
  <meta name="keywords" content="{{keywords}}" />
  <meta name="author" content="{{author}}" />
  
  <meta charset="utf-8" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1" />
  <meta name="description" content="">
  <meta name="keywords" content="" />
  <meta name="author" content="" />

  <meta name="viewport" content="width=device-width,initial-scale=1.0" />  
  <meta name="HandheldFriendly" content="True" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black" />

  <link rel="shortcut icon" href="/favicon.png" />
  <link rel="icon" href="/favicon.png" />

  <!-- apple splash screens
       check http://susy.oddbird.net/demos/magic/ -->
  <link href="img/splash-iphone.png" media="screen and (max-device-width: 480px) and not (-webkit-min-device-pixel-ratio: 2)" rel="apple-touch-startup-image">
  <link href="img/splash-iphone4.png" media="screen and (max-device-width: 480px) and (-webkit-min-device-pixel-ratio: 2)" rel="apple-touch-startup-image">
  <link href="img/splash-portrait.png" media="screen and (min-device-width: 768px) and (orientation: portrait)" rel="apple-touch-startup-image">
  <link href="img/splash-landscape.png" media="screen and (min-device-width: 768px) and (orientation: landscape)" rel="apple-touch-startup-image">

  <link href="/css/style.css" rel="stylesheet" type="text/css" />

  <!--[if lte IE 8]>
  <link rel="stylesheet" href="css/fallback.css" />
  <![endif]-->

  %#include other javascript at the end of the page to improve loading

  <script type="application/javascript">  
  </script>

</head>
<body>
  <!-- Prompt IE 6 users to install Chrome Frame. -->
  <!--[if lt IE 7]><p class=chromeframe>Your browser is <em>ancient!</em> <a href="http://browsehappy.com/">Upgrade to a different browser</a> or <a href="http://www.google.com/chromeframe/?redirect=true">install Google Chrome Frame</a> to experience this site.</p><![endif]-->
  <div class="page">

  %#include navigation active=active
  
  <div id="result"> </div>

  %#this is utilized by rebase calls
  %#easier than passing in body from application.py
  %include
	
  %#include footer
    
  </div><!-- END .page -->    

  <script>
    var _gaq=[['_setAccount','UA-XXXXX-X'],['_trackPageview']];
    (function(d,t){var g=d.createElement(t),s=d.getElementsByTagName(t)[0];
    g.src=('https:'==location.protocol?'//ssl':'//www')+'.google-analytics.com/ga.js';
    s.parentNode.insertBefore(g,s)}(document,'script'));
  </script>
  <!--[if lt IE 7 ]>
    <script defer src="//ajax.googleapis.com/ajax/libs/chrome-frame/1.0.3/CFInstall.min.js"></script>
    <script defer>window.attachEvent('onload',function(){CFInstall.check({mode:'overlay'})})</script>
  <![endif]-->
</body>
</html>
