    <header role="banner">
      <!--global site navigation-->
      <!--<nav role="sitenav" class="navbar navbar-inverse navbar-fixed-top">-->
      <nav role="sitenav" id="sitenav" class="navbar navbar-inverse">
	<div class="navbar-inner">
          <button type="button" class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>

	  <a href="/" title="Collections" class="home_link">
	    <div class="logo">
	      <img src="img/logo.png" alt="Collections Logo" /> Collections
	    </div>
	  </a>

          <div class="nav-collapse collapse">

	    <ul class="nav nav-pills">
	      <!-- consolidate between .active and #current ??? -->
	      %if active == "home":
	      <li class="active"><a href="/" id="current">Home</a></li>
	      %else:
	      <li class><a href="/">Home</a></li>
 	      %end

	      %if active == "help":
	      <li class="active"><a href="/help" id="current">Help</a></li>
	      %else:
	      <li class><a href="/help">Help</a></li>
 	      %end
	      
	    </ul>
	  </div> <!-- END .nav-collapse collapse -->
	</div> <!-- END .navbar-inner -->
      </nav>

    </header>
  
