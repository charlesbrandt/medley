<html>
<head>
  <title>{{ path }}</title>
  %include header description='', keywords='', author=''
  

  <script src="/js/sortable.js"></script>

  <style>
	/* remember: .class #id */
	.column { float: left }
	.group { padding: 5px; margin: 2px; border: 1px solid black; }
	.scroller {  
		  display:block
    		  width:100%;
    		  height:700px;
    		  overflow:auto
    		  }
	/* some items need a fixed width to get flow right:
	.widget { margin: 0 0px 0px 0; float: left; width: 206px; font-size: .7em; }
	*/

	/* or go dynamic.. it works if content is consistent:
	*/
	.widget { margin: 0 0px 0px 0; float: left; font-size: .7em; }
	.widget-content { padding: 0.3em; }

	.button { float: right;  margin: 0 15 0 0;  }
	.position { float: right; }
	.portlet-header { margin: 0.3em; padding-bottom: 4px; padding-left: 0.2em; }
	.portlet-header .ui-icon { float: right; }
	.ui-sortable-placeholder { border: 1px dotted black; visibility: visible !important; height: 50px !important; }
	.ui-sortable-placeholder * { visibility: hidden; }
	.row { clear: left; }
  </style>

</head>
<body>

<div id="result"> </div>

<div id="tabs">
  <ul>
    %count = -1
    %for key in tab_order:
    %  count += 1
    <li><a href="#tabs-{{ count }}">{{ key }}</a></li>
    %end
  </ul>

%number = -1
%for key in tab_order:
%  group = groups[key]
%  number += 1

  <div id="tabs-{{ number }}" class="scroller">
    Count: {{ len(group) }} <br>
    <div id="{{ key }}" class="column connectedSortable">

      %for item in group:
      <div class="widget" id="{{ item }}">
	<div class="widget-content">
	  %include file_summary path=item
	</div>
      </div>
      %end #for item in group:
      

    </div> 
  </div> 

  %end  #end for key, group in groups.items()
</div>

%#this is for giving javascript a way to find source destination
%#don't need to see it.
<div id="destination" style="display:none">{{ destination }}</div>



</body>
</html>

