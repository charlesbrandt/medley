<h1>  <a href="/person/{{ person.tag }}/">{{ person.name }}</a> </h1>

<h3 class="main_tag">{{ person.tag }}</h3>

%if person.tags:
<p>Also Known As:</p>
% other_tags = person.tags[:]
% other_tags.remove(person.tag)
%include tag_block tags=other_tags
%end

<p>Similar names:</p>
    %include people_block people=related

<ul id="people" class="content" data-bind='template: { name: "personTmpl", foreach: contents }'>
</ul>

<script id="personTmpl" type="text/html">
    <li class="draggable summary content" draggable="true" data-bind="css: { available: available}, event:{
       dragstart:   function(data, event){ 
                    $(event.target).addClass('dragSource')
                    $root.drag_start_index($index());
                    return $(event.target).hasClass('draggable');
       },    

       dragend:   function(data, event){  
                   $root.drag_start_index(-1);
                   $(event.target).removeClass('dragSource')
                   return true;
       },    
       
       dragover:  function(data, event){event.preventDefault();},

       dragenter: function(data, event){
                $root.drag_target_index($index());
                var element = $(event.target)
                if(element.hasClass('draggable'))
                     element.toggleClass('dragover'); 
                event.preventDefault();
       },

       dragleave: function(data, event, $index){
                var element = $(event.target)
                if(element.hasClass('draggable'))
                     element.toggleClass('dragover');
                event.preventDefault();
       },

       drop: function(data, event){
                $(event.target).removeClass('dragover'); 
                //console.log('swap', $root.drag_start_index(),  $root.drag_target_index() );
                $root.move($root.drag_start_index(),  $root.drag_target_index());
		$root.post();
       }

}">

	<div class="wrapper"> 
	  <div class="wrapper" data-bind="if: image"> 
	    <a data-bind="attr: { href: '/collection/' + collection + '/content/' + content_base }"><img data-bind="attr: { src: '/path/' + image }" class="thumb"></a>
	  </div>
	    
	  <a data-bind="attr: { href: '/collection/' + collection + '/content/' + content_base }"><b data-bind='text: title'></b></a>
	</div>


	<ul data-bind="foreach: people">
	  <li class="person"><a data-bind="attr: { href: '/person/' + $data + '/' }, text: $data"></a></li>
	</ul>
	
	<ul data-bind="foreach: tags" class="tags">
	  <li class="tag"><a data-bind="attr: { href: '/tag/' + $data }, text: $data"></a></li>
	</ul>
	
	
	<p data-bind="text: description, style: {'display': 'none'}"></p>
	
	<p>
	  <img data-bind="click: $parent.move_to_top" src="/img/arrow-up.svg" width="25" />
	  <input size="4" data-bind="value: position" />
	  <img data-bind="click: $parent.move_to_bottom" src="/img/arrow-down.svg" width="25" />
	</p>
	<p>
	  Via: <a data-bind="attr: { href: '/collection/' + collection }, text: collection"></a>
	</p>
	
    </li>
</script>

<script type="text/javascript">
  var contents = {{! contents }};
</script>

  <script type="text/javascript">window.JSON || document.write('<script src="js/lib/json2.js"><\/script>')</script>
    
    <script type="text/javascript" src="/js/lib/require.js"></script>
    <script type="text/javascript">
      //this allows require.js to be in a different directory (lib)
      //than main custom code
      require.config({
		baseUrl: '/js',
		paths: {
			'jquery' : 'lib/jquery-2.0.3',
	                'lodash' : 'lib/lodash',
	                'ko'     : 'lib/knockout-3.0.0'
		}
      });
      require(['person'], function(person) {});
    </script>

%rebase layout title=str(person.tag), active="home"
