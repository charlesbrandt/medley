<html>
<head>
  <title></title>
  %include header description='', keywords='', author=''

  <link rel="stylesheet" href="/css/jquery-ui.css" media="screen" type="text/css" />

  <!--
   from:
   http://code.google.com/apis/libraries/devguide.html#jqueryUI
      
   <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.6.1/jquery.min.js"></script>
  <script src="/js/jquery/1.6.1/jquery.min.js"></script>
  <script src="file:///c/technical/web/template/js/jquery/1.6.1/jquery.js"></script>


   <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.4.4/jquery.min.js"></script>
  <script src="/js/jquery-1.4.4.min.js"></script>
  <script src="file:///c/technical/web/template/js/jquery/1.4.4/jquery.js"></script>

   <script src="https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.13/jquery-ui.min.js"></script>
  -->
  <script src="/js/jquery/1.6.1/jquery.min.js"></script>
  <script src="/js/jqueryui/1.8.18/jquery-ui-1.8.18.custom.min.js"></script>
  <!--
  <script src="file:///c/technical/web/template/js/jqueryui/1.8.13/jquery-ui.js"></script>

  <script src="/js/jquery.mobile-1.0a2.min.js"></script>  
  <script src="/js/processing-1.0.0.min.js"></script>  
  <script src="/js/raphael-min.js"></script>  

  <script src="file:///c/moments2/moments2/journal.js"></script>
  -->
  <script src="/js/custom.js"></script>


  <script language="javascript">
$(document).ready(function(){
   /* Description:

   */
   // Your code here

 });

$(function() {
   // this works!!:
   var availableTags = [
      "Java",
      "Javascript",
      "Perl",
      "PHP",
      "Python",
      "Ruby",
   ];
   $("input#tags").autocomplete({source: availableTags});
   /*
   $("input#tags").autocomplete({source: "http://localhost:8088/search/",
                                 select: function(event, ui) {
                                         window.location='/tagged/'+ui.item.value; }
                                  });
   */


		$( ".column" ).sortable({
			connectWith: ".column"
		});

		$( ".portlet" ).addClass( "ui-widget ui-widget-content ui-helper-clearfix ui-corner-all" )
			.find( ".portlet-header" )
				.addClass( "ui-widget-header ui-corner-all" )
				.prepend( "<span class='ui-icon ui-icon-minusthick'></span>")
				.end()
			.find( ".portlet-content" );

		$( ".portlet-header .ui-icon" ).click(function() {
			$( this ).toggleClass( "ui-icon-minusthick" ).toggleClass( "ui-icon-plusthick" );
			$( this ).parents( ".portlet:first" ).find( ".portlet-content" ).toggle();
		});

		$( ".column" ).disableSelection();

});


  </script>

  <style>
	.column { width: 170px; float: left; padding-bottom: 100px; }
	.portlet { margin: 0 1em 1em 0; }
	.portlet-header { margin: 0.3em; padding-bottom: 4px; padding-left: 0.2em; }
	.portlet-header .ui-icon { float: right; }
	.portlet-content { padding: 0.4em; }
	.ui-sortable-placeholder { border: 1px dotted black; visibility: visible !important; height: 50px !important; }
	.ui-sortable-placeholder * { visibility: hidden; }
	</style>

</head>
<body>
  %include navigation

<div id="result"> </div>

<div>
<div class="column">

	<div class="portlet">
		<div class="portlet-header">Feeds</div>
		<div class="portlet-content">Lorem ipsum dolor sit amet, consectetuer adipiscing elit</div>
	</div>
	
	<div class="portlet">
		<div class="portlet-header">News</div>
		<div class="portlet-content">Lorem ipsum dolor sit amet, consectetuer adipiscing elit</div>
	</div>

</div>

<div class="column">

	<div class="portlet">
		<div class="portlet-header">Shopping</div>
		<div class="portlet-content">Lorem ipsum dolor sit amet, consectetuer adipiscing elit</div>
	</div>

</div>

<div class="column">

	<div class="portlet">
		<div class="portlet-header">Links</div>
		<div class="portlet-content">Lorem ipsum dolor sit amet, consectetuer adipiscing elit</div>
	</div>
	
	<div class="portlet">
		<div class="portlet-header">Images</div>
		<div class="portlet-content">Lorem ipsum dolor sit amet, consectetuer adipiscing elit</div>
	</div>

</div>

</div>



search for entries based on tags<br>
tag search field<br>
should autocomplete with available options<br>

<label for="tags">Tags: </label>
<input id="tags" value=''>
<input type=button name="submit" value="Go" onClick="window.location='/tagged/test'+$('input#tags').value;">

  
  {{! body }}

  %include footer

</body>
</html>

<html>
<head>
  <title></title>


   

  </script>

</head>
<body>

</body>
</html>
