<h3>  <a href="/collection/{{ str(summary) }}">{{ str(summary) }}</a> </h3>

  {{ len(c) }} items in collection <br>
  loaded from {{ c.source }}<br>
  
  <br>

  {{ len(cluster) }} items in cluster<br><br>

  %for group in cluster:
     %for item in group:
       <a href="/collection/{{ str(summary) }}/person/{{ item }}">{{ item }}</a>
     %end
     <br>
  %end




  <div>
  %if len(summary.available) == 1:
  [ drive available! ]
  %elif len(summary.available):
  [ {{ len(summary.available) }} drives available! ]
  %end

  </div><br>

%rebase layout title=str(summary), active="home"
