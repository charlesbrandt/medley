<h3><a href="/collections">Collections: ({{len(collections)}})</a></h3>

<ul>
%for collection in collections:
  %#include collection_short collection=collection
  <li class="item">
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
  </div><br>
  </li>

% end #for collection
</ul>

<h3><a href="/people">People</a></h3>

%rebase layout title="Medley!", active="home"
