
  {{ len(cluster) }} items in cluster<br><br>

  %for group in cluster:
     %for item in group:
       <a href="/collection/{{ str(summary) }}/person/{{ item }}">{{ item }}</a>
     %end
     <br>
  %end

  <div>
  </div><br>

%rebase layout title=str(summary), active="home"
