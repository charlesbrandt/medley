<ul>
%for item in people:
  <li><a href="/person/{{ item.tag }}">{{ item.tag }}</a></li>
%end
</ul>
