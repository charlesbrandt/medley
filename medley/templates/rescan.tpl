<h3>  <a href="/collection/{{ str(collection.summary) }}">{{ str(collection.summary) }}</a> </h3>

loaded from: {{ str(collection.source) }}<br>
walked? {{ collection.walk }}<br>

  <div>
  %if len(collection.summary.available) == 1:
  [ drive available! ]
  %elif len(collection.summary.available):
  [ {{ len(collection.summary.available) }} drives available! ]
  %end

<br>
  {{ len(collection.summary.metas.items()) }} meta jsons.<br>
  % for meta in collection.summary.metas.keys():
  &nbsp;&nbsp;(<a href="/list/{{ str(collection) }}/meta/{{ str(meta) }}/0/100">list</a>) (<a href="/sort/{{ str(collection) }}/meta/{{ str(meta) }}">sort</a>) (<a href="/collection2/{{ str(collection) }}/meta/{{ str(meta) }}">c2</a>) <a href="/collection/{{ str(collection) }}/meta/{{ str(meta) }}">{{ str(meta) }}</a> 

  %if collection.summary.metas[meta]['length']:
  ( {{ collection.summary.metas[meta]['length'] }} items as of: {{ collection.summary.metas[meta]['updated'] }} )
  %end
<br>

  %if collection.summary.metas[meta].has_key('orders'):
  %for o in collection.summary.metas[meta]['orders']:
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;   (<a href="/collection2/{{ str(collection) }}/meta/{{ str(meta) }}/{{ str(o) }}">{{ str(o) }}</a>) <br>
  %end
  %end

  %end #for meta

  </div><br>

%rebase layout title=str(collection.summary), active="home"
