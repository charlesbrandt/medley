<h3>  <a href="/person/{{ person.tag }}">{{ person.name }}</a> </h3>

<p class="tag">Main Tag: {{ person.tag }}</p>

<p>Other tags:</p>
<ul>
%for tag in person.tags:
  <li>{{tag}}</li>
%end
</ul>

<p>Similar names:</p>
<ul>
%for item in related:
  <li><a href="/person/{{ item.tag }}">{{ item.tag }}</a></li>
%end
</ul>


%rebase layout title=str(person.tag), active="home"
