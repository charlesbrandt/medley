
<ul id="buttons" class="content" data-bind="foreach: cluster.groups">
  <li class="content" data-bind="ifnot: items()[0].tag === 'empty'"><button class="button" type="button" data-bind="click: $root.show($index()), text: $index() + '. ' + items()[0].tag + ' (' + items().length + ')'"></button></li>
</ul>

<ul id="cluster" class="content" data-bind="foreach: cluster.groups">
  <div class="wrapper" data-bind="if: $root.showing() === $index()">
    <ul id="people" class="content" data-bind="template: { name: 'personTmpl', foreach: items }, scrollableOnDragOver: 'scroll-while-dragging'"> 
    </ul>
  </div>
  

</ul>

<script id="personTmpl" type="text/html">
    <li class="draggable summary content block" draggable="true" data-bind="event:{
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
		//console.log('index: ' + $index());
		//console.log(ko.dataFor(event.target));
		ko.dataFor(event.target).move($root.drag_start_index(), $root.drag_target_index());
		$root.cluster.post();
       }

}">

	<p class="position">
	  <img class="icon" data-bind="click: $parent.move_to_top" src="/img/arrow-up.svg" />
	  <input size="4" data-bind="value: position" />
	  <img class="icon" data-bind="click: $parent.move_to_bottom" src="/img/arrow-down.svg" />
	</p>

	<div class="wrapper"> 
	  <div class="wrapper" data-bind="if: image"> 
	    <a data-bind="attr: { href: '/person/' + tag + '/'}"><img class="lazy thumb" data-bind="lazyImage: imageUrl" /></a>
	  </div>
	    
	  <div class="person_name">
            <span class="name_background">
              <span class="content_count">(<span data-bind="text: cutoffs + '/' + count, visible: count"></span>)</span><span class="spacer"></span>
              <br>
              <span class="spacer"></span>
              <a class="name_link" data-bind="attr: { href: '/person/' + tag + '/' }"><b data-bind='text: tag'></b></a> 
            </span>
          </div>

        </div>
	
	
    </li>
</script>

<script type="text/javascript" src="/js/lib/jquery-1.10.2.min.js"></script>

<script type="text/javascript">
  var ogroups = {{! people_json }};
  //console.log(ogroups);
</script>

<script type="text/javascript">window.JSON || document.write('<script src="js/lib/json2.js"><\/script>')
  </script>
    
  <script type="text/javascript" src="/js/lib/jquery-1.10.2.js"></script>
  <script type="text/javascript" src="/js/lib/jquery.viewport.mini.js"></script>
  <script type="text/javascript" src="/js/lib/lodash.js"></script>
  <script type="text/javascript" src="/js/lib/knockout-3.0.0.js"></script>
  <script type="text/javascript" src="/js/people.js"></script>


%rebase layout title="People", active="home"
