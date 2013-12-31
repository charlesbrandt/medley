
  {{ len(cluster) }} items in cluster<br><br>


    %for group in cluster:
      <ul>
      %for item in group:
      % person = people.get_first(item)
        <li class="summary content">
	  %if person and person.image:
	  <div><a href="/person/{{ item }}/"><img src="blank.png" data-src="/path/{{person.image}}" class="thumb"></a></div>
	  %end
	  <a href="/person/{{ item }}/">{{ item }}</a>
	</li>
      %end
      </ul>
    <br>
  %end

  <div>
  </div><br>

<script type="text/javascript" src="/js/lib/jquery-2.0.3.min.js"></script>
<script type="text/javascript" src="/js/lib/jquery.unveil.min.js"></script>

<script type="text/javascript">
  var people = {{! people_json }};

$(document).ready(function() {
  $("img").unveil(200);
});
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
      require(['people'], function(people) {});
    </script>

%rebase layout title="People", active="home"
