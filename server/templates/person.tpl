<div class="leftcolumn">

<p class="expand-one"><a href="#">Similar names:</a> ({{len(related)}})</p>
<div class="content-one">
    %include people_block people=related
</div>

<p>Similar to:
<span data-bind="visible: !editing_similar(), html: similar_links, click: edit_similar"></span>
<input data-bind="visible: editing_similar(), value: similar, hasFocus: editing_similar">
<img src="/img/edit.png" class="icon" data-bind="visible: !editing_similar(), click: edit_similar">
</p>

<div><p>Download photos:
<img src="/img/edit.png" class="icon" data-bind="click: toggle_downloads">
</p>
<textarea placeholder="urls" data-bind="visible: editing_downloads(), value: photo_urls"></textarea>
<input placeholder="tags" data-bind="visible: editing_downloads(), value: photo_tags">
<button data-bind="visible: editing_downloads(), click: do_download">Download</button>
</div>

<h3 class="main_tag">{{ person.tag }} (<b>{{ len(person.contents) }}</b> items)</h3>

% other_tags = person.tags[:]
% other_tags.remove(person.tag)
%if other_tags:
<p>Also known as:</p>
%include tag_block tags=other_tags
%end


</div>



<div class="rightcolumn">

<p>Links:
<a href="http://www.google.com/search?q={{ person.split_tag() }}">google</a>
<span data-bind="visible: !editing_links(), foreach: link_lines, click: edit_links">
  <span data-bind="html: $data"></span>
</span>
<textarea data-bind="visible: editing_links(), value: links, hasFocus: editing_links" rows="4" cols="50"></textarea>
<img src="/img/edit.png" class="icon" data-bind="visible: !editing_links(), click: edit_links">

<br>Notes:
<b data-bind="visible: !editing_notes(), text: notes, click: edit_notes"></b>
<textarea data-bind="visible: editing_notes(), value: notes, hasFocus: editing_notes" rows="4" cols="50"></textarea>
<img src="/img/edit.png" class="icon" data-bind="visible: !editing_notes(), click: edit_notes">
</p>

<p>Cutoffs: 
<input data-bind="visible: editing_cutoffs(), value: cutoffs, hasFocus: editing_cutoffs">
<img src="/img/edit.png" class="icon" data-bind="visible: !editing_cutoffs(), click: edit_cutoffs">
Cutoff tags: 
<input data-bind="visible: editing_cutoff_tags(), value: cutoff_tags, hasFocus: editing_cutoff_tags">
<img src="/img/edit.png" class="icon" data-bind="visible: !editing_cutoff_tags(), click: edit_cutoff_tags">
Default tag: 
<input data-bind="visible: editing_default_cutoff_tag(), value: default_cutoff_tag, hasFocus: editing_default_cutoff_tag">
<b data-bind="visible: !editing_default_cutoff_tag(), text: default_cutoff_tag, click: edit_default_cutoff_tag"></b>
<img src="/img/edit.png" class="icon" data-bind="visible: !editing_default_cutoff_tag(), click: edit_default_cutoff_tag">
Default cutoff: 
<input data-bind="visible: editing_default_cutoff(), value: default_cutoff, hasFocus: editing_default_cutoff">
<b data-bind="visible: !editing_default_cutoff(), text: default_cutoff, click: edit_default_cutoff"></b>
<img src="/img/edit.png" class="icon" data-bind="visible: !editing_default_cutoff(), click: edit_default_cutoff">
</p>

<b data-bind="visible: !editing_cutoffs() && !editing_cutoff_tags(), text: merged_cutoffs"></b>

<p>
</p>

</div>

<span id="toggle-layout">Column direction</span>
<span id="show-photos">Toggle Photos</span>
<span id="show-media">Toggle Content</span>
<div class="row"></div>

<div class="scroll-while-dragging" data-bind="with: scrollWhileDragging">
  <ul id="photos" class="content top-bottom-columns" data-bind="foreach: items, scrollableOnDragOver: 'scroll-while-dragging'">
    <li data-bind="
                   css: { dragging: dragging },
                   dragZone: { name: 'scroll-while-dragging',
                   dragStart: $parent.dragStart,
                   dragEnd: $parent.dragEnd
                   },
                   dragEvents: {
                   name: 'scroll-while-dragging',
                   dragOver: $parent.reorder,
                   data: { items: $parent.items, item: $data }
                   }">
      <img data-bind="attr: { src: '/path/' + value.drive_dir + '/' + value.base_dir + '/' + value.filename }" class="thumb"></a>
    </li>
  </ul>
</div>


<ul id="content" class="content top-bottom-columns" data-bind='template: { name: "contentTmpl", foreach: contents }'>
</ul>

<script id="contentTmpl" type="text/html">
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

	<p class="position">
	  <img class="icon" data-bind="click: $parent.move_to_top" src="/img/arrow-up.svg" />
	  <input size="4" data-bind="value: position" />
	  <img class="icon" data-bind="click: $parent.move_to_bottom" src="/img/arrow-down.svg" />
	</p>


	<div class="wrapper"> 
	  <div class="wrapper" data-bind="if: image"> 
	    <a data-bind="attr: { href: '/collection/' + collection + '/content/' + base_dir }"><img data-bind="attr: { src: '/path/' + image }" class="thumb"></a>
	  </div>
	    
	  <a data-bind="attr: { href: '/collection/' + collection + '/content/' + base_dir }"><b data-bind='text: title'></b></a>
	</div>


	<ul data-bind="foreach: people">
	  <li class="person"><a data-bind="attr: { href: '/person/' + $data + '/' }, text: $data"></a></li>
	</ul>
	
	<ul data-bind="foreach: tags" class="tags">
	  <li class="tag"><a data-bind="attr: { href: '/tag/' + $data }, text: $data"></a></li>
	</ul>
	
	
	<p data-bind="text: description, style: {'display': 'none'}"></p>
	
	<p class="tag">
	  <span data-bind="text: timestamp"></span>, Via: <a data-bind="attr: { href: '/collection/' + collection }, text: collection"></a>
	</p>
	
    </li>
</script>

<script type="text/javascript">
  var contents = {{! contents }};
  var photos = {{! photos }};
  var cur_person = {{! person.as_json() }};
</script>


<script type="text/javascript" src="/js/lib/jquery-1.10.2.js"></script>
<script type="text/javascript" src="/js/lib/lodash.js"></script>
<script type="text/javascript" src="/js/lib/knockout-3.0.0.js"></script>
<script type="text/javascript" src="/js/lib/knockout.dragdrop.js"></script>
<script type="text/javascript" src="/js/person.js"></script>

%rebase layout title=str(person.tag), active="home"
