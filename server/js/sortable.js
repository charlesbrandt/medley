$(document).ready(function(){
	function save_tabs_array() {
	    /* this version generates an Array of results to send back
	     */
	    var result = new Array(0);
	    $('.column').each(function(index) {
		    result.push($(this).sortable('toArray'));
		});
	    var cloud = JSON.stringify(result, null, 2);
	    $.post("/save_tabs", { 'cloud': cloud } );	
	}

	function save_tabs() {
	    /* trying to create a dictionary instead 
	       (dictionaries in javascript are basic objects)
	     */
	    var result = {};
	    $('.column').each(function(index) {
		    result[$(this).attr("id")] = $(this).sortable('toArray');
		    //result.push($(this).sortable('toArray'));
		});
	    var cloud = JSON.stringify(result, null, 2);
	    var destination = "/save_tabs" + $("#destination").text();
	    //alert(destination);
	    //$.post("/save_tabs", { 'cloud': cloud } );	
	    $.post(destination, { 'cloud': cloud } );	
	    //alert(result.length);
	}

	var $tabs = $( "#tabs" ).tabs();
	
	var $tab_items = $( "ul:first li", $tabs ).droppable({
		accept: ".connectedSortable div",
		hoverClass: "ui-state-hover",
		drop: function( event, ui ) {
		    var $item = $( this );
		    var $list = $( $item.find( "a" ).attr( "href" ) )
		    .find( ".connectedSortable" );
		    
		    ui.draggable.hide( "slow", function() {
			    //$tabs.tabs( "select", $tab_items.index( $item ) );
			    $( this ).appendTo( $list ).show( "slow" );
			});
		    //save with every drop elsewhere
		    //save_tabs();
		}
	    });

    
	$( ".column" ).sortable({
		connectWith: ".column",
		    update: function(event, ui) {
		    //save with every move:
		    save_tabs();
		    /*
		    var result = new Array(0);
		    $('.column').each(function(index) {
			    result.push($(this).sortable('toArray'));
			});
		    var cloud = JSON.stringify(result, null, 2);
		    $.post("/save_tabs", { 'cloud': cloud } );	
		    */
		}
	    });

	//optionally provide a manual way to save
	$("#save_tabs").click(function(event) {
		event.preventDefault();
		save_tabs();
	    });
	
	$( ".column" ).disableSelection();
	
	// how much to account for bottom part of page: 
	var adjuster = 64;
	//set the right height for our scroller div initially
	$(".scroller").css("height", $(window).height() - ($("#tabs > ul").height()+adjuster) );
	
	//update it again any time we resize the window
	$(window).resize(function() {
		$(".scroller").css("height", $(window).height() - ($("#tabs > ul").height()+adjuster) );
	});
	
    });

