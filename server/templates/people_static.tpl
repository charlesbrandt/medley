    %for group in cluster:
      <ul>
      %for item in group:
      % person = people.get_first(item)
        <li class="summary content">
	  %if person and person.image:
	  <div><a href="/person/{{ item }}/"><img src="/img/blank.jpg" data-src="/path/{{person.image}}" class="thumb"></a></div>
	  %end
	  <a href="/person/{{ item }}/">{{ item }}</a>
	</li>
      %end
      </ul>
    <br>
  %end

  <div>
  </div><br>

  {{ len(cluster) }} items in cluster<br><br>

<script type="text/javascript" src="/js/lib/jquery-2.0.3.min.js"></script>
<script type="text/javascript" src="/js/lib/jquery.unveil.min.js"></script>

<script type="text/javascript">
$(document).ready(function() {
  $("img").unveil(200);
});
</script>

%rebase layout title="People", active="home"
