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
  
  %include head 

  <script type="application/javascript">  
  </script>

</head>
<body>
  <!-- Prompt IE 6 users to install Chrome Frame. -->
  <!--[if lt IE 7]><p class=chromeframe>Your browser is <em>ancient!</em> <a href="http://browsehappy.com/">Upgrade to a different browser</a> or <a href="http://www.google.com/chromeframe/?redirect=true">install Google Chrome Frame</a> to experience this site.</p><![endif]-->
  <div class="page">

  %include navigation active=active
  
  <div id="result"> </div>

  %#this is utilized by rebase calls
  %#easier than passing in body from application.py
  %include
	
  %include footer
    
  </div><!-- END .page -->    

  <script src="//ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"></script>
  <script>window.jQuery || document.write('<script src="js/libs/jquery-1.7.1.min.js"><\/script>')</script>

  <!-- these should all be minified and combined before a production release -->
  <script src="js/libs/util.js"></script>
  <script src="js/plugins.js"></script>
  <script src="js/script.js"></script>

  <script src="js/libs/bootstrap-button.js"></script>
  <script src="js/libs/bootstrap-collapse.js"></script>

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
