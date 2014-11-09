
<!--<input data-bind="textInput: search"> knockout 3.2-->
<input data-bind="value: search, valueUpdate: 'afterkeydown'">
<span data-bind="text: number"></span><span data-bind="visible: number() > cutoff"> (too many!) </span>

<!--
<ul id="people" class="content" data-bind="foreach: results"> 
  <li data-bind="text: tag"></li>
</ul>
-->

<ul id="cluster" class="content">
  <div class="wrapper">
    <ul id="people" class="content" data-bind="template: { name: 'personTmpl', foreach: results }"> 
    </ul>
  </div>
</ul>

<script id="personTmpl" type="text/html">
    <li class="summary content block">
	<div class="wrapper"> 
	  <div class="wrapper"> 
	    <a data-bind="attr: { href: '/person/' + tag + '/'}">
              <!--<img class="lazy thumb" data-bind="lazyImage: imageUrl" />-->
              <img class="thumb" data-bind="attr: { src: imageAuto }" />
            </a>
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
  var opeople = {{! people_json }};
  var onames = {{! names_json }};
  //console.log(opeople);
</script>

<script type="text/javascript">window.JSON || document.write('<script src="js/lib/json2.js"><\/script>')
  </script>
    
  <script type="text/javascript" src="/js/lib/jquery-1.10.2.js"></script>
  <script type="text/javascript" src="/js/lib/lodash.js"></script>
  <script type="text/javascript" src="/js/lib/knockout-3.0.0.js"></script>
  <script type="text/javascript" src="/js/search.js"></script>


%rebase layout title="Search", active="home"
