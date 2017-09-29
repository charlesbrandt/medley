%if content.available:

<div class="summary available">
%if content.image:
<div><a href="/collection/{{content.remainder['collection'] }}/content/{{ content.remainder['original_base_dir'] }}"><img src="/path/{{content.image}}" class="thumb"></a></div>
%end
<a href="/collection/{{content.remainder['collection'] }}/content/{{ content.remainder['original_base_dir'] }}"><b>{{ content.title }}</b></a>


%else:

<div class="summary">
%if content.image:
<div><img src="/path/{{content.image}}" class="thumb"></div>
%end
<b>{{ content.title }}</b>

%end



%# not exactly the same: include people_block people=content.people
<ul>
%for tag in content.people:
  <li class="person"><a href="/person/{{ tag }}/">{{ tag }}</a></li>
%end
</ul>

%#<p>Tags:</p>
%include tag_block tags=content.tags


%#<p>{{ content.description }}</p>

<p>Via: <a href="/collection/{{ content.remainder['collection'] }}">{{ content.remainder['collection'] }}</a></p>
%#<p>available? {{ content.available }}</p>

%#<p>{{ content.remainder }}</p>
%#<p>{{ content.debug() }}</p>


</div>
