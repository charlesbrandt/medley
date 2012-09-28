<h3>All Collections: ({{len(collections)}})</h3>
%for collection in collections:
  %#include collection_short collection=collection
  <div>
  <a href="/collection/{{ str(collection) }}">{{ str(collection) }}</a> 
  <a href="/rescan/{{ str(collection) }}"><img src="/img/reload.svg" width=20 opacity="50%"></a>
  %if len(collection.available) == 1:
  [ drive available! ]
  %elif len(collection.available):
  [ {{ len(collection.available) }} drives available! ]
  %end

<br>
  {{ len(collection.metas.items()) }} meta jsons.<br>
  % for meta in collection.metas.keys():
  &nbsp;&nbsp;(<a href="/list/{{ str(collection) }}/meta/{{ str(meta) }}/0/100">list</a>) (<a href="/sort/{{ str(collection) }}/meta/{{ str(meta) }}">sort</a>) (<a href="/collection2/{{ str(collection) }}/meta/{{ str(meta) }}">c2</a>) <a href="/collection/{{ str(collection) }}/meta/{{ str(meta) }}">{{ str(meta) }}</a> 

  %if collection.metas[meta]['length']:
  ( {{ collection.metas[meta]['length'] }} items as of: {{ collection.metas[meta]['updated'] }} )
  %end
<br>

  %if collection.metas[meta].has_key('orders'):
  %for o in collection.metas[meta]['orders']:
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;   (<a href="/collection2/{{ str(collection) }}/meta/{{ str(meta) }}/{{ str(o) }}">{{ str(o) }}</a>) <br>
  %end
  %end

  %end #for meta

  </div><br>

% end
%rebase layout title="All Collections", active="home"
