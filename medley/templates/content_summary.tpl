<div class="summary">
<h4>{{ content.title }}</h4>

%# not exactly the same: include people_block people=content.people
<ul>
%for tag in content.people:
  <li><a href="/person/{{ tag }}">{{ tag }}</a></li>
%end
</ul>

<p>Tags:</p>
%include tag_block tags=content.tags

<p>{{ content.description }}</p>

<p>Collection: {{ content.remainder['collection'] }}</p>
<p>available?</p>

%#<p>{{ content.remainder }}</p>
%#<p>{{ content.debug() }}</p>


</div>
