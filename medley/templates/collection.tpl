<h3>  <a href="/collection/{{ str(summary) }}">{{ str(summary) }}</a> </h3>

% index = summary.scraper.local_index()
{{!index}}
    

  <div>
  %if len(summary.available) == 1:
  [ drive available! ]
  %elif len(summary.available):
  [ {{ len(summary.available) }} drives available! ]
  %end

<br>
  {{ len(summary.metas.items()) }} meta jsons.<br>
  % for meta in summary.metas.keys():
  &nbsp;&nbsp;(<a href="/list/{{ str(summary) }}/meta/{{ str(meta) }}/0/100">list</a>) (<a href="/sort/{{ str(summary) }}/meta/{{ str(meta) }}">sort</a>) (<a href="/collection2/{{ str(summary) }}/meta/{{ str(meta) }}">c2</a>) <a href="/collection/{{ str(summary) }}/meta/{{ str(meta) }}">{{ str(meta) }}</a> 

  %if summary.metas[meta]['length']:
  ( {{ summary.metas[meta]['length'] }} items as of: {{ summary.metas[meta]['updated'] }} )
  %end
<br>

  %if summary.metas[meta].has_key('orders'):
  %for o in summary.metas[meta]['orders']:
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;   (<a href="/collection2/{{ str(summary) }}/meta/{{ str(meta) }}/{{ str(o) }}">{{ str(o) }}</a>) <br>
  %end
  %end

  %end #for meta

  </div><br>

%rebase layout title=str(summary), active="home"
